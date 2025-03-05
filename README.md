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
