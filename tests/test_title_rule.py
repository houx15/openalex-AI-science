from src.data.title_rule import review_abstract, review_title, review_title_old


def test_reviews_excluded():
    for t in ["A Survey on Oversmoothing in Graph Neural Networks", "Adversarial Training: A Survey",
              "Machine Learning and Port Scans: A Systematic Review", "Lecture Notes on Computerized Tomography",
              "Comment on: Thermodynamic determination of the equilibrium line", "A Perspective on Quantum Sensors",
              "Some topics in Sasakian geometry, a survey", "Review of Cetacean's click detection algorithms"]:
        assert review_title(t), t


def test_research_kept():
    for t in ["The MAGPI Survey: Impact of environment on the total internal mass distribution of galaxies",
              "An ALMA spectroscopic survey of the Planck high-redshift object PLCK G073.4-57.5",
              "Localized covariance estimation: A Bayesian perspective",
              "Zero-shot Generative Large Language Models for Systematic Review Screening Automation",
              "Large Language Models Show Human-like Social Desirability Biases in Survey Responses"]:
        assert not review_title(t), t
        assert review_title_old(t), t  # all excluded by the Phase 0 rule


def test_whitespace_and_abstract():
    assert review_title("A Survey\n  of Generative Retrieval")
    assert review_abstract("This review attempts to explain the theory.")
    assert not review_abstract("We surveyed 58 respondents.")
