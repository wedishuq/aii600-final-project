# AII 600 final project

Fork this repository once per project. The fork tracks the code and the documents. The documents are the proposal, the presentation, and `decisions.md`, which is the history of what was done and why.

Follow the [final project lab](https://vsokolov.org/labs/final-project-lab.html) from the question through the decision to the short presentation. The strawberry harvest on that page is the worked example. Your project is your own hypothesis, your own data, and a decision someone will make differently because of the model. `CHECKLIST.md` is the lab's "In your project" boxes. The ticks on the lab page are saved in that browser only. `CHECKLIST.md` is the list that counts.

## Who
Project Member/s
* Abel Rezene
* Given the sensitivity of the proposed data, I will be the only project member.
<!-- Alone, or a group of at most three. One person forks. That person adds the other members and `VadimSokolov` as collaborators. On a repository owned by a personal account the role is Write. On the fork, write the names and GitHub usernames under this heading. One person speaks at the presentation. Every member can explain the whole repository.-->

## Fork

The repository is public, and so is the fork.

1. Fork https://github.com/VadimSokolov/aii600-final-project.
2. On the fork, open Settings, then General, then Features. Turn Issues on. Leave Pull requests on. The starter has them off, so a request cannot land there. A fork has them on.
3. Settings, then Collaborators. Add teammates and `VadimSokolov`. The role is Write.
4. Install the [GitHub CLI](https://cli.github.com/) and [Quarto](https://quarto.org/docs/get-started/). Run `gh auth login`. Clone your fork. Python projects: before the first notebook run, replace `x.y.z` in `.python-version` with the version number of the kernel you run it with, for example `3.12.4`. In that clone, run `gh repo set-default OWNER/REPO` with your fork, so `gh` does not act on the starter. A branch that has not been merged to `main` and pushed is not submitted.
5. The invitation expires after seven days. Send it when the fork exists. If it expires before 28 October, send it again.

Feedback comes back as an issue on the fork. I add the labels `proposal`, `preliminary`, and `final`. The issue is a comment on the work. It does not contain a score.

## Changes

`main` is the submitted project, and it stays runnable. A person working alone may commit to `main`. A group does not. Branch from `main`, make one change, and open a pull request. Set the base repository to your fork, not `VadimSokolov/aii600-final-project`. The starter does not accept pull requests. Another member reads the request and merges it. The request names the `decisions.md` entry it carries out, and that entry is part of the same merge. The commit message says why. Do not force-push `main`.

Two people do not edit `analysis.ipynb` on two branches at once. A function you both change goes in a `.py` or `.R` file, and the notebook calls it. Before a checkpoint merge, run the notebook from the top and commit it with the outputs saved. Save the plots in `fig/`.

`requirements.txt` lists the packages the notebook imports, with versions, for the interpreter in `.python-version`. Python projects: that file holds the version number of the kernel that runs the notebook, for example `3.12.4`. An R project deletes both files and commits `renv.lock` instead. That file records the R version. Do not commit data files, secrets, or fitted weights. A key stays in `.env`. When the terms allow you to republish the files, they go on the release tagged `data`, and that release exists by 18 November. When they do not, `data/README.md` gives the command that downloads the files from the source. A weight file the talk needs goes on a release. If a result depends on a random draw, the `decisions.md` entry records the seed.

## Checkpoints

The times are 7:00 pm Eastern. The submission is what has been pushed to `main` on GitHub before then. The time that counts is the push GitHub recorded, not the date on the commit.

- Proposal, 28 October. `PROPOSAL.md`, at most one page, with the three headings already in that file. The first entry in `decisions.md` records that choice and the alternative you set aside.
- Preliminary results, 18 November. `analysis.ipynb` has the raw-data plot, the summary table, the split, one baseline, one model, and both held-out scores in the units of the decision. `decisions.md` has an entry for the split, the model, and the loss.
- Final presentation, 9 December. `presentation.html` is the presentation. `decisions.md` runs from the proposal to the action on the first content slide. The repository meets `CHECKLIST.md`. The talk is that night, 7:30 to 10:15 pm. Three minutes, the same length for one person and for a group.

A late push still gets a comment, and the issue says it was late. The checkpoints have no separate points. If `main` is not on GitHub when you are scheduled to present, that slot waits until it is, and no later than 16 December.

## The talk

The talk is `presentation.html`, opened in a browser. It is a title slide plus four slides: the action, the reason, the risk of that action with a number, and what it is worth to be less wrong. Do not add slides. The risk is a probability or a cost the decision maker can use. The held-out score, in the units of the decision, stays in `analysis.ipynb` and has to agree with the reason slide. Edit `presentation.qmd`, then render it:

```bash
quarto render presentation.qmd
```

Render it once, in the commit you will present, and commit both files. The HTML is large, and two people cannot merge it. The code and the plots stay in the repository.

## Data

Leave the data files out of git. A file you are allowed to republish goes on the GitHub release tagged `data`. The release is public. A file the terms let you download but not republish stays off the release: `data/README.md` gives the command that fetches it from the source. The notebook reads a local copy from `data/` either way.

## Tools

R or Python. Use the language you can explain. AI assistants are allowed. On your fork, add one line to this README: what you used, and for what. You are responsible for everything on `main`, including the parts you did not write.

## Files

- `PROPOSAL.md`. The proposal. Replace the prompts. Leave the headings.
- `presentation.qmd` and `presentation.html`. The talk. A title slide and four slides. Replace the prompts. Leave the headings.
- `decisions.md`. Append one entry per choice. Do not rewrite an old entry.
- `CHECKLIST.md`. The lab, as checkboxes. Tick them in the final commit.
- `analysis.ipynb`. The code, and the home of the diagram, the equations, the simulation check, the residuals and calibration, and the limits. A `.py` or `.R` file holds a function two people would otherwise edit in the notebook.
- `requirements.txt` and `.python-version`. The packages, and the interpreter they were pinned for. An R project deletes both and commits `renv.lock`.
- `.github/pull_request_template.md`. The form a pull request opens with.
- `fig/`. Plots saved from the notebook, including `fig/layers.png`.
- `data/README.md`. The source, the file names, and the commands that publish or download the data.
