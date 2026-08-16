This dataset is sourced from the paper titled "DeepPull: Deep Learning-Based Approach for Predicting Reopening, Decision, and Lifetime of Pull Requests on GitHub Open-Source Projects" by P. Banyongrakkul and S. Phoomvuthisarn.

The dataset comprises 288,121 pull requests from 83 open-source projects on GitHub spanning 6 programming languages: Python, R, Java, Ruby, PHP, and C++. These pull requests were created between August 2010 and September 2023.

The dataset includes 30 tabular features, as listed in the table below, along with 2 textual features (e.g., title and body), 3 target features (e.g., reopening, decision, and lifetime), and 5 metadata features, described as follows:

- created_at (datetime): The date and time when the pull request was submitted.
- closed_at (datetime): The date and time when the pull request was closed.
- PJ_pc_commits_by_pr_NNULL (boolean): Indicates the validity of the "pc of commits made by pr" feature (1: valid, 0: invalid due to division by zero).
- PJ_file_rejected_proportion_NNULL (boolean): Indicates the validity of the "file rejected proportion" feature (1: valid, 0: invalid due to division by zero).
- CT_age_NNULL (boolean): Indicates whether the contributor age feature is present (1: not missing, 0: missing).


*__List of tabular features__*
| #  | Feature                      | Source          | Description                                                                                     |
|----|------------------------------|-----------------|-------------------------------------------------------------------------------------------------|
| 1  | \# of commits                | Pull request    | Number of commits in the pull request                                                            |
| 2  | \# of modified files         | Pull request    | Number of files modified in the pull request                                                     |
| 3  | \# of added files            | Pull request    | Number of files added by the pull request                                                        |
| 4  | \# of deleted files          | Pull request    | Number of files deleted in the pull request                                                      |
| 5  | \# of changed files          | Pull request    | Number of files changed by the pull request                                                      |
| 6  | \# of changed src files      | Pull request    | Number of source files changed by the pull request                                               |
| 7  | \# of changed test files     | Pull request    | Number of test files changed by the pull request                                                 |
| 8  | \# of changed doc files      | Pull request    | Number of document files changed by the pull request                                             |
| 9  | \# of changed other files    | Pull request    | Number of other files changed by the pull request                                                |
| 10 | \# of changed lines          | Pull request    | Number of lines changed by the pull request                                                       |
| 11 | \# of added lines            | Pull request    | Number of lines added by the pull request                                                         |
| 12 | \# of deleted lines          | Pull request    | Number of lines deleted by the pull request                                                       |
| 13 | has test                     | Pull request    | If the pull request contains any test file                                                        |
| 14 | \# of changes test lines     | Pull request    | Number of test lines changed by the pull request                                                  |
| 15 | has pr link                  | Pull request    | If the description of the pull request has any pull request link                                   |
| 16 | \# of previous pr in project | Project         | Number of previous pull requests received by the project                                          |
| 17 | \% of commits made by pr     | Project         | Percent of commits made by pull requests in the last month                                        |
| 18 | \# of commits files touched  | Project         | Number of total commits on files changed by the pull request 3 months before                      |
| 19 | file rejected proportion     | Project         | Percent of previously rejected pull requests in files changed by the pull request               |
| 20 | \# of merged pr              | Project         | Number of merged pull requests in the latest 10 pull requests                                     |
| 21 | \# of rejected pr            | Project         | Number of rejected pull requests in the latest 10 pull requests                                   |
| 22 | is recent pr rejected        | Project         | If the latest pull request is rejected                                                            |
| 23 | reputation                   | Contributor     | Percent of the contributor’s previous accepted pull requests                                      |
| 24 | is first pr                  | Contributor     | If the contributor has no experience in submitting pull requests                                 |
| 25 | contributor age              | Contributor     | Time, in minutes, since the contributor became a GitHub user                                      |
| 26 | \# of events in pr           | Contributor     | Number of interactions of the contributor in pull requests                                        |
| 27 | \# of comments in pr         | Contributor     | Number of comments of the contributor in pull requests                                            |
| 28 | \# of commits prev pr        | Contributor     | Number of commits of the contributor                                                                |
| 29 | \# of previous pr created    | Contributor     | Number of pull requests submitted by the contributor                                                |
| 30 | is core team                 | Contributor     | If the contributor is a core team member for the project                                            |
