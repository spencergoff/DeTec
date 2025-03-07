# Overview

DeTec is an electronic component search engine. Users input electronic circuit requirements in plain English and get links to components as output. 

![detec-poc-screenshot](https://github.com/user-attachments/assets/41abb6cd-16e5-4ba2-914e-33b83671b40d)


The site can be reached here: https://d3r9mhcj5ucoi7.cloudfront.net/ 

The ultimate goal is for DeTec to be a copilot for circuit design engineers.

# Problem Statement

It takes circuit design engineers hours or days to search for off-the-shelf ICs that meet their requirements. Filtering options on sites such as DigiKey are numerous, and often the engineer has to sift through dozens of search results and analyze each datasheet before determining which results (if any) meet the requirements. 

# Status

DeTec component search has the reached proof-of-concept state, meaning that the site sometimes returns accurate search results for basic queries. 

# Tech Stack

Our current tech stack consists of:
* Nova Pro LLM (from Amazon)
* AWS Lambda, S3, and CloudFront
* Nexar API (formerly aprt of Octopart; used for component searching)
* Python, Javascript, HTML

![DeTec-v01-architecture-diagram](https://github.com/user-attachments/assets/dbb8d984-1bfe-451e-ab8b-8876f0965129)


# Road Map

We're tracking most tasks publicly here: https://github.com/users/spencergoff/projects/1/views/1

At the time of writing, the next major tasks are:
* Creating a dataset to evaluate the search engine performance
* Trying to use a web search tool instead of the Nexar API (goals: improved search results, no reliance on Nexar API subscription/tokens, and low cost)
* Allowing for up to 20 requirements per query
* Supporting results that require multiple components

# Demo

Proof-of-concept demo of the DeTec component search engine is here: https://youtu.be/YRZwEUJqhIU

# Evaluation

We will judge the accuracy of our system by how it performs against the tests in the tests/circuit_requirements.yaml file. Each test case is a potential user query which only has one or a handful of correct answers, and is assigned a difficulty level based on these criteria: 
1. A query with 1-5 basic requirements.
2. A query with 5-10 basic requirements.
3. A query with 5-10 requirements, including at least 2 intermediate requirements.
4. A query with 8-10 requirements, including at least 2 intermediate requirements and 1 complex requirement. 
5. A query with more than 10 requirements, including at least 3 intermediate requirements and 2 or more complex requirements.

Requirement difficulty definitions:
* A basic requirement is one which is readily available via common component search APIs and component landing pages using simple text extraction.
* An intermediate requirment is one which requires either applying math operations to find the correct component (e.g. quiescent current less than 10 mA, as opposed to equals 10 mA) or understanding charts in component datasheets.
* A complex requirement is one which requires domain knowledge and complex reasoning.

Each release of the application will be tagged with a score. A score is calculated by dividing the number of points the application gets by the total number of possible points in the evaluation set. Correctly guessing the answer to a test case with a difficulty of 3 will give the application 3 points, and so on.

Each test case will come from a real-world scenario.