# Re-test of SPEC §9's three-way period fixed effects with R fixest (docs/DEVIATIONS.md, 2026-11-06).
#
# pyfixest 0.60.0 PPML did not converge with field x career bin x half-year effects on 30k-50k-author
# samples. This script fits the Phase 0 power-simulation model on the same inputs with fixest::fepois
# under both specifications and records convergence, run time and the W / WI-W standard errors:
#   additive : n ~ W_post + WI_post + I_post | author + field x half + career x half + exposure bin x half
#   threeway : n ~ W_post + WI_post + I_post | author + field x career x half + exposure bin x half
# Inputs are 2018H1-2022H2 eligible-work counts (no later outcomes, no scores); author types are drawn
# at random (true effect zero), mid scenario of src/analysis/sim_power.py. Panel construction mirrors
# sim_power.build_panel and fe_groups.add_period_fe.
#
# Usage: Rscript src/analysis/fe_threeway_check.R PANEL_CSV AUTHORS_CSV OUT_CSV [SIZES]

suppressPackageStartupMessages({ library(data.table); library(fixest) })
args <- commandArgs(trailingOnly = TRUE)
sizes <- if (length(args) >= 4) as.integer(strsplit(args[4], ",")[[1]]) else c(30000L, 100000L, 1000000L)
SEED <- 20261116L
HALVES <- (2018L * 2L):(2022L * 2L + 1L)
GAP <- 2021L * 2L
POST_START <- 2021L * 2L + 1L
MIN_AUTHORS <- 500L
FIELD_DOMAIN <- c(setNames(rep("1", 5), c("11", "13", "24", "28", "30")),
                  setNames(rep("2", 6), c("12", "14", "18", "20", "32", "33")),
                  setNames(rep("3", 10), c("15", "16", "17", "19", "21", "22", "23", "25", "26", "31")),
                  setNames(rep("4", 5), c("27", "29", "34", "35", "36")))
setFixest_nthreads(as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", "4")))

a <- fread(args[2], colClasses = list(character = c("author_id", "modal_field")))
a[, n_i := pmin(n_arxiv_elig, 3L)]
a[, exp_bin := as.integer(cut(n_arxiv_elig, c(0, 1, 2, 3, 5, Inf))) - 1L]
a[, fid := fifelse(is.na(modal_field) | modal_field == "", "none", sub(".*/", "", modal_field))]
cnt <- fread(args[1], select = c("author_id", "half", "n"), colClasses = list(character = "author_id"))

build <- function(sub) {
  g <- CJ(author_id = sub$author_id, half = HALVES)
  g <- merge(g, sub[, .(author_id, first_year, fid, n_i, exp_bin)], by = "author_id")
  g <- g[half >= pmax(first_year * 2L, HALVES[1])]
  g <- merge(g, cnt, by = c("author_id", "half"), all.x = TRUE)
  g[is.na(n), n := 0L]
  age <- g$half %/% 2L - g$first_year
  g[, career := as.character(cut(age, c(-Inf, 5, 10, 20, Inf), labels = c("0-5", "6-10", "11-20", "21+")))]
  g <- g[half != GAP]
  g[, post := as.integer(half >= POST_START)]
  size <- sub[, .N, by = fid]
  big <- size[N >= MIN_AUTHORS, fid]
  dom <- FIELD_DOMAIN[g$fid]
  g[, fgroup := fifelse(fid %in% big, fid, paste0("domain/", fifelse(is.na(dom), "none", dom)))]
  g
}

draw_types <- function(sub, p_w = 0.15, p_i_w = 0.25, p_i_nw = 0.02) {
  n <- sub$n_i
  wf <- rbinom(length(n), n, p_w)
  if_ <- rbinom(length(n), wf, p_i_w) + rbinom(length(n), n - wf, p_i_nw)
  w <- wf / n >= 0.5; i <- if_ / n >= 0.5
  data.table(author_id = sub$author_id, W = as.integer(w & !i), WI = as.integer(w & i), I = as.integer(!w & i))
}

fit_one <- function(d, spec) {
  fml <- if (spec == "additive") {
    n ~ W_post + WI_post + I_post | author_id + fgroup^half + career^half + exp_bin^half
  } else {
    n ~ W_post + WI_post + I_post | author_id + fgroup^career^half + exp_bin^half
  }
  t0 <- Sys.time()
  m <- tryCatch(fepois(fml, data = d, cluster = ~author_id, fixef.iter = 100000, glm.iter = 100, notes = FALSE),
                error = function(e) e)
  secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  if (inherits(m, "error")) return(list(spec = spec, ok = FALSE, error = conditionMessage(m), seconds = secs))
  b <- coef(m); v <- vcov(m)
  list(spec = spec, ok = TRUE, error = "", seconds = secs, converged = isTRUE(m$convStatus),
       glm_iter = m$iterations, nobs = nobs(m), n_fe = paste(m$fixef_sizes, collapse = "/"),
       b_w = b[["W_post"]], se_w = sqrt(v["W_post", "W_post"]),
       b_wi_minus_w = b[["WI_post"]] - b[["W_post"]],
       se_wi_minus_w = sqrt(v["W_post", "W_post"] + v["WI_post", "WI_post"] - 2 * v["W_post", "WI_post"]))
}

set.seed(SEED)
rows <- list()
for (size in sizes) {
  sub <- if (size >= nrow(a)) a else a[sample(.N, size)]
  p <- build(sub)
  cat(sprintf("authors %d: %d rows, %d field groups, %d field x career x half cells\n", nrow(sub), nrow(p),
              uniqueN(p$fgroup), uniqueN(p[, .(fgroup, career, half)])))
  for (rep in 1:2) {
    d <- merge(p, draw_types(sub), by = "author_id")
    for (t in c("W", "WI", "I")) set(d, j = paste0(t, "_post"), value = d[[t]] * d$post)
    for (spec in c("additive", "threeway")) {
      r <- c(list(authors = nrow(sub), rep = rep), fit_one(d, spec))
      print(unlist(r)); flush.console()
      rows[[length(rows) + 1]] <- r
      fwrite(rbindlist(rows, fill = TRUE), args[3])
    }
  }
}
cat("fixest", as.character(packageVersion("fixest")), "| R", R.version.string, "\n")
