# Crowd-Audit: Crowdsourcing Audits with End Users

Crowd-Audit facilitates crowdsourced audits done by end (lay) users, which enables faster and more thorough audits. While Crowd-Audit’s current implementation currently focuses on the Perspective API, it can be extended to other open source algorithms.

## Problem:
Audits take a long time to conduct, which means that many AI systems in need of auditing are not audited. For instance, an algorithmic auditing consultancy executive stated that audits can take six to nine months to complete. Much of this time is spent on testing hypotheses and identifying areas for improvement.

In addition, audits today are done by experts. Given experts' limited time and small number, audits are limited by the cases the experts decide to test.

## Solution:
Crowd-Audit addresses both problems by introducing a tool that will make audits faster to conduct and more thorough. It features a web-application that collects multiple end (lay) users’ audits of a system. Crowd-Audit also has an aggregator that condenses the multitude of user reports into a single report that enables experts to see areas of improvement.

While both the web-application and aggregator are currently focused on Perspective API, it can be modified to extend to other open source AI applications. (Perspective API estimates a comment’s toxicity and is used in content moderation on social media, such as in the New York Times.) This extension is particularly easy for other NLP-based algorithms. 

The web-application collects multiple users’ audits by having end users:
1) label examples from the Perspective API dataset,
2) extend end users’ expectations by training a personalized model predicting on previously unseen models,
3) examine examples in which the end users’ model estimates a toxicity score wildly differs from the perspective API,
4) submit pertinent examples along with a summary of thoughts about these examples (i.e., a user report).  


This web-application is **Indielabel**, "an interactive web application for end-user auditing" that was introduced in Lam et. al's **End-User Audits: A System Empowering Communities to Lead Large-Scale Investigations of Harmful Algorithmic Behavior** paper. You can see the original repo at: https://github.com/StanfordHCI/indie-label. (Anticipated next steps would be to make the implementation more modular/generic so that it can be easily extended to other open source algorithms.)

The aggregator automatically filters the wheat from the chaff by condensing users’ reports into a single one. This report includes user summaries/suggestions as well as commonly submitted examples. To filter out bad actors, the aggregator only accepts data from users who have submitted examples that have been brought up in other users’ reports. In addition, the report shows the most important information for each of the examples. Experts have the option to read individual users’ reports by going to the log of individual user reports.

---
# IndieLabel (i.e., the Web Application)

## IndieLabel Installation / Setup
- Activate your virtual environment (tested with Python 3.8).
- Install requirements:
    ```
    $ pip install -r requirements.txt
    ```
- Download and unzip the `data` sub-directory from [this Drive folder](https://drive.google.com/file/d/1In9qAzV5t--rMmEH2R5miWpZ4IQStgFu/view?usp=sharing) and place it in the repo directory (334.2MB zipped, 549.1MB unzipped).


- Start the Flask server:
    ```
    $ python server.py
    ```

- Concurrently build and run the Svelte app in another terminal session:
    ```
    $ cd indie_label_svelte/
    $ HOST=0.0.0.0 PORT=5000 npm run dev autobuild
    ```

- You can now visit `localhost:5001` to view the IndieLabel app!

## IndieLabel: Main paths
Here's a summary of the relevant pages used for each participant in our study. For easier setup and navigation, we added URL parameters for the different labeling and auditing modes used in the study.
- Participant's page: `localhost:5001/?user=<USER_NAME>`
- Labeling task pages:
    - Group-based model (group selection): `localhost:5001/?user=<USER_NAME>&tab=labeling&label_mode=3`
    - End-user model (data labeling): `localhost:5001/?user=<USER_NAME>&tab=labeling&label_mode=0`
- Tutorial page: `localhost:5001/?user=DemoUser&scaffold=tutorial `
- Auditing task pages:
    - Fixed audit, end-user model: `localhost:5001/?user=<USER_NAME>&scaffold=personal`
    - Fixed audit, group-based model: `localhost:5001/?user=<USER_NAME>&scaffold=personal_group`
    - Free-form audit, end-user model: `localhost:5001/?user=<USER_NAME>&scaffold=prompts` 

## IndieLabel: Setting up a new model
- Set up your username and navigate to the **Labeling** page 
    - Option A: Using a direct URL parameter
        - Go to `localhost:5001/?user=<USER_NAME>&tab=labeling&label_mode=0`, where in place of `<USER_NAME>`, you've entered your desired username
    - Option B: Using the UI
        - Go to the Labeling page and ensure that the "Create a new model" mode is selected.
        - Select the User button on the top menu and enter your desired username.

- Label all of the examples in the table
    - When you're done, click the "Get Number of Comments Labeled" button to verify the number of comments that have been labeled. If there are at least 40 comments labeled, the "Train Model" button will be enabled.
    - Click on the "Train Model" button and wait for the model to train (~30-60 seconds).

- Then, go to the **Auditing** page and use your new model.
    - To view the different auditing modes that we provided for our evaluation task, please refer to the URL paths listed in the "Auditing task pages" section above.

---
# Aggregator

## Aggregator Installation / Setup

Make sure to follow the instructions/setup in IndieLabel. The aggregator assumes that you have also set up the data sub-directory and have at least 1 user report submitted.

- Run the aggregator:
    ```
    $ python aggregateUserReports.py
    ```
The report will appear in the aggregated_user_reports.txt file in the main directory.
