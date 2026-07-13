# scripts/mock_resumes.py
"""
20 hand-written mock resumes spanning diverse fields, used to evaluate the
keyword pre-filter's recall/precision at a larger, more statistically
meaningful scale than the 2 real users we had (services/keyword_matcher.py,
jobs/extract_keywords.py). Written with common resume conventions (summary,
skills, experience with bullet points, education) rather than keyword-stuffed
text, so keyword extraction quality is representative of real usage.

Includes a mix of roles that should match plenty of postings in the
telegram_messages channels (backend/frontend/devops/data/mobile/etc.) and a
few unrelated-field controls (nurse, sales, accountant) to sanity-check that
the filter doesn't over-match unrelated postings.
"""

MOCK_RESUMES = [
    {
        "name": "Backend Engineer (Java/Spring)",
        "resume": """
Amir Rezaei
Backend Software Engineer
Tehran, Iran | amir.rezaei.dev@example.com | +98 912 000 0001

PROFESSIONAL SUMMARY
Backend engineer with 5 years of experience designing and building scalable
Java microservices. Strong background in Spring Boot, distributed systems,
and relational databases. Comfortable owning services end-to-end from design
through production monitoring.

SKILLS
Java, Spring Boot, Spring Cloud, Hibernate, PostgreSQL, MySQL, Kafka, Redis,
Docker, Kubernetes, REST APIs, gRPC, JUnit, Maven, Git, CI/CD (Jenkins)

WORK EXPERIENCE
Senior Backend Engineer, Digikala — Jan 2023 to Present
- Designed and maintained a payments microservice processing 2M+ transactions/day.
- Migrated a monolithic order service into Spring Boot microservices, cutting
  average response time by 40%.
- Introduced Kafka-based event streaming between order and inventory services.

Backend Engineer, Snapp — Jun 2020 to Dec 2022
- Built REST APIs for the driver-matching service using Java and Spring Boot.
- Optimized PostgreSQL queries, reducing p95 latency from 800ms to 150ms.
- Wrote integration tests with JUnit and Testcontainers.

EDUCATION
B.Sc. in Computer Engineering, Amirkabir University of Technology — 2016-2020
""",
    },
    {
        "name": "Frontend Developer (React/Vue)",
        "resume": """
Sara Ahmadi
Frontend Developer
Isfahan, Iran | sara.ahmadi.frontend@example.com

SUMMARY
Frontend developer with 4 years of experience building responsive,
accessible web applications with React and Vue. Passionate about component
design systems and performance optimization.

SKILLS
JavaScript (ES6+), TypeScript, React, Redux, Vue.js, Next.js, HTML5, CSS3,
Tailwind CSS, SASS, Webpack, Vite, Jest, Cypress, Figma, Git

EXPERIENCE
Frontend Developer, Snapp Market — 2022 to Present
- Built and maintained the customer-facing checkout flow in React and TypeScript.
- Migrated legacy jQuery pages to a React + Redux architecture.
- Reduced bundle size by 35% via code splitting and lazy loading.

Junior Frontend Developer, Divar — 2020 to 2022
- Developed reusable UI components in Vue.js used across five product teams.
- Collaborated with designers in Figma to implement pixel-accurate layouts.

EDUCATION
B.Sc. in Software Engineering, University of Isfahan — 2016-2020
""",
    },
    {
        "name": "Full-Stack Developer (Node/React)",
        "resume": """
Kaveh Moradi
Full-Stack Developer

SUMMARY
Full-stack developer with 3+ years of experience across the entire web
stack — from Node.js APIs to React frontends. Comfortable working in small
teams and shipping features quickly.

SKILLS
JavaScript, TypeScript, Node.js, Express, React, Next.js, MongoDB,
PostgreSQL, GraphQL, Docker, AWS (EC2, S3, Lambda), Git

EXPERIENCE
Full-Stack Developer, a small e-commerce startup — 2021 to Present
- Built the entire backend API in Node.js/Express and the storefront in
  Next.js.
- Integrated payment gateways and shipping providers.
- Deployed and maintained infrastructure on AWS using Docker containers.

Freelance Web Developer — 2019 to 2021
- Delivered custom websites and small web apps for local businesses using
  the MERN stack.

EDUCATION
B.Sc. in Computer Science, Shiraz University — 2015-2019
""",
    },
    {
        "name": "DevOps Engineer (AWS/Kubernetes)",
        "resume": """
Reza Karimi
DevOps Engineer

PROFESSIONAL SUMMARY
DevOps engineer with 6 years of experience automating infrastructure and CI/CD
pipelines for high-traffic services. Deep expertise in Kubernetes, Terraform,
and AWS.

SKILLS
AWS, Kubernetes, Docker, Terraform, Ansible, Jenkins, GitLab CI, Prometheus,
Grafana, ELK Stack, Bash, Python, Linux administration, Helm

EXPERIENCE
Senior DevOps Engineer, Cafe Bazaar — 2021 to Present
- Migrated on-prem infrastructure to a Kubernetes cluster on AWS EKS.
- Built Terraform modules to provision infrastructure across three
  environments (dev/staging/prod).
- Set up Prometheus + Grafana monitoring stack with on-call alerting.

DevOps Engineer, Digikala — 2018 to 2021
- Automated deployment pipelines with Jenkins and GitLab CI.
- Managed Docker Swarm clusters before migrating to Kubernetes.

EDUCATION
B.Sc. in Information Technology, K. N. Toosi University — 2013-2017
""",
    },
    {
        "name": "Data Scientist (Python/ML)",
        "resume": """
Niloofar Hosseini
Data Scientist
niloofar.h.ds@example.com

SUMMARY
Data scientist with 4 years of experience building predictive models and
data pipelines. Strong statistics background with hands-on experience taking
models from research to production.

SKILLS
Python, Pandas, NumPy, Scikit-learn, PyTorch, TensorFlow, SQL, Spark,
Airflow, Jupyter, A/B testing, statistical modeling, feature engineering

EXPERIENCE
Data Scientist, Snapp — 2022 to Present
- Built a churn-prediction model that reduced customer attrition by 12%.
- Designed and ran A/B tests for pricing experiments.
- Built ETL pipelines in Airflow to feed the recommendation system.

Data Analyst, Tap30 — 2020 to 2022
- Built dashboards and reports for the operations team using SQL and Python.
- Performed exploratory analysis to identify demand patterns by city.

EDUCATION
M.Sc. in Statistics, Sharif University of Technology — 2018-2020
B.Sc. in Mathematics, Sharif University of Technology — 2014-2018
""",
    },
    {
        "name": "Data Engineer (Spark/Airflow)",
        "resume": """
Pouya Ghasemi
Data Engineer

SUMMARY
Data engineer with 5 years building large-scale data pipelines and
warehouses. Experienced with both batch and streaming architectures.

SKILLS
Python, Scala, Apache Spark, Apache Kafka, Airflow, Snowflake, BigQuery,
PostgreSQL, dbt, Docker, AWS (S3, Glue, Redshift), Git

EXPERIENCE
Senior Data Engineer, Digikala — 2021 to Present
- Built a streaming pipeline with Kafka and Spark Structured Streaming
  processing 5TB/day of clickstream data.
- Designed the company's dbt-based data warehouse on Snowflake.

Data Engineer, a fintech startup — 2019 to 2021
- Built batch ETL pipelines in Airflow orchestrating Spark jobs on AWS EMR.

EDUCATION
B.Sc. in Computer Engineering, Ferdowsi University of Mashhad — 2014-2018
""",
    },
    {
        "name": "iOS Developer (Swift)",
        "resume": """
Maryam Sadeghi
iOS Developer

SUMMARY
iOS developer with 4 years of experience shipping consumer apps used by
millions of users, with a focus on clean architecture and smooth UX.

SKILLS
Swift, SwiftUI, UIKit, Combine, Core Data, XCTest, Xcode, REST APIs,
MVVM, Git, Fastlane, App Store submission process

EXPERIENCE
iOS Developer, Snapp — 2022 to Present
- Rebuilt the driver app's onboarding flow in SwiftUI, cutting drop-off by 18%.
- Maintained a large UIKit codebase while gradually migrating to SwiftUI.

iOS Developer, Digikala — 2020 to 2022
- Implemented offline-first caching using Core Data for the shopping app.
- Wrote unit and UI tests with XCTest, raising code coverage from 40% to 75%.

EDUCATION
B.Sc. in Software Engineering, Iran University of Science and Technology — 2016-2020
""",
    },
    {
        "name": "Android Developer (Kotlin)",
        "resume": """
Hamed Jafari
Android Developer

SUMMARY
Android developer with 5 years of experience building native Android
applications in Kotlin, with strong focus on Jetpack Compose and modern
Android architecture.

SKILLS
Kotlin, Java, Jetpack Compose, Android Jetpack (Room, ViewModel, Navigation),
Coroutines, Dagger/Hilt, Retrofit, JUnit, Espresso, Git, Firebase

EXPERIENCE
Senior Android Developer, Cafe Bazaar — 2021 to Present
- Led migration of the app store client from Java/XML views to Kotlin +
  Jetpack Compose.
- Introduced Hilt for dependency injection across the app.

Android Developer, Divar — 2019 to 2021
- Built the listings feature using MVVM architecture and Kotlin Coroutines.
- Integrated Firebase Analytics and Crashlytics.

EDUCATION
B.Sc. in Computer Engineering, University of Tehran — 2015-2019
""",
    },
    {
        "name": "QA / Test Automation Engineer",
        "resume": """
Elham Karimi
QA Automation Engineer

SUMMARY
QA engineer with 4 years of experience building automated test suites for
web and mobile applications, with a strong focus on CI integration.

SKILLS
Selenium, Cypress, Playwright, Appium, Python, JavaScript, Postman, JIRA,
TestRail, Jenkins, Git, API testing, performance testing (JMeter)

EXPERIENCE
QA Automation Engineer, Tap30 — 2022 to Present
- Built an end-to-end Cypress test suite covering the booking flow.
- Integrated automated tests into the Jenkins CI pipeline, catching
  regressions before release.

QA Engineer, Snapp Market — 2020 to 2022
- Wrote manual and automated test cases for the checkout flow.
- Used Postman and JMeter for API and load testing.

EDUCATION
B.Sc. in Computer Science, Shahid Beheshti University — 2016-2020
""",
    },
    {
        "name": "Site Reliability Engineer",
        "resume": """
Farhad Tehrani
Site Reliability Engineer

SUMMARY
SRE with 6 years of experience ensuring high availability for large-scale
distributed systems. Strong background in incident response, observability,
and capacity planning.

SKILLS
Kubernetes, Terraform, Prometheus, Grafana, PagerDuty, Go, Python, AWS, GCP,
Linux, Bash, distributed systems, on-call incident management, SLOs/SLIs

EXPERIENCE
Senior SRE, Digikala — 2020 to Present
- Defined SLOs/SLIs for the checkout service and built dashboards to track them.
- Led incident response for major outages, writing post-mortems and driving
  remediation.
- Automated capacity planning using historical traffic data.

Systems Engineer, Cafe Bazaar — 2017 to 2020
- Maintained on-prem and cloud infrastructure, migrating services to
  Kubernetes over 18 months.

EDUCATION
B.Sc. in Computer Engineering, Sharif University of Technology — 2013-2017
""",
    },
    {
        "name": "Cloud Architect (Azure)",
        "resume": """
Bahar Yousefi
Cloud Solutions Architect

SUMMARY
Cloud architect with 8 years of experience designing enterprise-scale
cloud infrastructure, primarily on Microsoft Azure. Certified Azure
Solutions Architect Expert.

SKILLS
Microsoft Azure, Azure DevOps, Terraform, Kubernetes (AKS), networking,
identity & access management, cost optimization, disaster recovery,
PowerShell, Python, security architecture

EXPERIENCE
Cloud Architect, a large telecom company — 2019 to Present
- Designed the company's landing zone architecture across Azure subscriptions.
- Led migration of 40+ legacy applications to Azure, reducing infra cost by 25%.
- Defined enterprise security and networking standards for cloud workloads.

Infrastructure Engineer, an enterprise IT consultancy — 2015 to 2019
- Designed hybrid cloud networking between on-prem data centers and Azure.

EDUCATION
M.Sc. in Information Systems, University of Tehran — 2013-2015
B.Sc. in Computer Engineering, University of Tehran — 2009-2013

CERTIFICATIONS
Microsoft Certified: Azure Solutions Architect Expert
""",
    },
    {
        "name": "Cybersecurity Engineer",
        "resume": """
Arman Faraji
Cybersecurity Engineer

SUMMARY
Cybersecurity engineer with 5 years of experience in application security,
penetration testing, and security operations.

SKILLS
Penetration testing, OWASP Top 10, Burp Suite, Nmap, Metasploit, SIEM
(Splunk), network security, threat modeling, Python, incident response,
ISO 27001, vulnerability management

EXPERIENCE
Security Engineer, a fintech company — 2021 to Present
- Performed penetration tests on web and mobile applications, identifying
  critical vulnerabilities before release.
- Built a SIEM dashboard in Splunk for real-time threat detection.
- Led incident response for a phishing campaign targeting employees.

SOC Analyst, a managed security services provider — 2019 to 2021
- Monitored security alerts and triaged incidents across client environments.

EDUCATION
B.Sc. in Computer Engineering, Amirkabir University of Technology — 2015-2019
""",
    },
    {
        "name": "Machine Learning Engineer (NLP/LLMs)",
        "resume": """
Yasaman Rostami
Machine Learning Engineer

SUMMARY
ML engineer with 4 years of experience building and deploying NLP models,
including recent work fine-tuning and deploying LLMs in production.

SKILLS
Python, PyTorch, Hugging Face Transformers, LangChain, LLMs, prompt
engineering, RAG pipelines, vector databases (Pinecone, FAISS), Docker,
FastAPI, MLOps, model deployment

EXPERIENCE
ML Engineer, an AI startup — 2022 to Present
- Built a RAG-based customer support assistant using LangChain and a
  fine-tuned open-source LLM.
- Deployed models behind a FastAPI service with autoscaling on Kubernetes.

NLP Engineer, a research lab — 2020 to 2022
- Fine-tuned transformer models for Persian text classification.
- Built data pipelines for training corpus collection and cleaning.

EDUCATION
M.Sc. in Artificial Intelligence, Sharif University of Technology — 2018-2020
""",
    },
    {
        "name": "UI/UX Designer",
        "resume": """
Golnaz Amini
UI/UX Designer

SUMMARY
Product designer with 5 years of experience designing user-centered
interfaces for web and mobile products, from research through high-fidelity
prototypes.

SKILLS
Figma, Sketch, Adobe XD, user research, wireframing, prototyping, design
systems, usability testing, interaction design, accessibility (WCAG)

EXPERIENCE
Senior Product Designer, Divar — 2021 to Present
- Led the redesign of the listing creation flow, increasing completion rate
  by 22%.
- Built and maintained the company's design system in Figma.
- Ran usability testing sessions to validate design decisions.

UX Designer, Cafe Bazaar — 2019 to 2021
- Designed onboarding flows for the app store client.
- Collaborated closely with frontend engineers to ensure design fidelity.

EDUCATION
B.A. in Graphic Design, Tehran University of Art — 2015-2019
""",
    },
    {
        "name": "Blockchain Developer",
        "resume": """
Danial Kazemi
Blockchain Developer

SUMMARY
Blockchain developer with 3 years of experience building smart contracts
and decentralized applications on Ethereum and EVM-compatible chains.

SKILLS
Solidity, Ethereum, Hardhat, Foundry, Web3.js, Ethers.js, smart contract
security, IPFS, JavaScript, TypeScript, Node.js

EXPERIENCE
Blockchain Developer, a DeFi startup — 2022 to Present
- Built and audited smart contracts for a token-staking protocol.
- Wrote a frontend dApp using React and Ethers.js to interact with contracts.

Junior Blockchain Developer, a Web3 agency — 2021 to 2022
- Developed NFT minting smart contracts using Solidity and Hardhat.

EDUCATION
B.Sc. in Computer Engineering, Iran University of Science and Technology — 2017-2021
""",
    },
    {
        "name": "Game Developer (Unity/C#)",
        "resume": """
Shayan Moradi
Game Developer

SUMMARY
Game developer with 4 years of experience building mobile and PC games in
Unity, from gameplay systems to performance optimization.

SKILLS
Unity, C#, game design, gameplay programming, 3D math, shader basics,
mobile game optimization, Git, Photon (multiplayer networking)

EXPERIENCE
Game Developer, a mobile game studio — 2021 to Present
- Built core gameplay systems for a mobile puzzle game with 1M+ downloads.
- Optimized rendering performance to hit 60fps on low-end Android devices.

Junior Game Developer, an indie studio — 2020 to 2021
- Implemented multiplayer features using Photon networking.

EDUCATION
B.Sc. in Computer Science, Azad University — 2016-2020
""",
    },
    {
        "name": "Embedded Systems Engineer (C/C++)",
        "resume": """
Omid Salehi
Embedded Systems Engineer

SUMMARY
Embedded systems engineer with 6 years of experience developing firmware
for IoT and industrial devices in C and C++.

SKILLS
C, C++, embedded Linux, RTOS (FreeRTOS), microcontrollers (ARM Cortex-M),
UART/SPI/I2C, firmware development, JTAG debugging, Python (tooling)

EXPERIENCE
Senior Embedded Engineer, an industrial IoT company — 2020 to Present
- Developed firmware for a fleet of IoT sensors running FreeRTOS on ARM
  Cortex-M microcontrollers.
- Designed communication protocols over UART and SPI between subsystems.

Embedded Software Engineer, an automotive supplier — 2017 to 2020
- Wrote low-level drivers for automotive sensor modules in C.

EDUCATION
B.Sc. in Electrical Engineering, Sharif University of Technology — 2013-2017
""",
    },
    {
        "name": "Database Administrator (PostgreSQL/Oracle)",
        "resume": """
Nasrin Ebrahimi
Database Administrator

SUMMARY
DBA with 7 years of experience managing high-availability PostgreSQL and
Oracle databases for high-traffic production systems.

SKILLS
PostgreSQL, Oracle, MySQL, database replication, backup and recovery,
performance tuning, query optimization, index design, Linux, Bash,
monitoring (Prometheus, pgAdmin)

EXPERIENCE
Senior DBA, Digikala — 2019 to Present
- Managed a PostgreSQL cluster handling 10K+ queries per second.
- Led a migration from Oracle to PostgreSQL for the inventory system.
- Set up streaming replication and automated failover.

Database Administrator, a banking software vendor — 2015 to 2019
- Administered Oracle databases for core banking applications.
- Performed regular performance tuning and capacity planning.

EDUCATION
B.Sc. in Computer Engineering, Isfahan University of Technology — 2011-2015
""",
    },
    {
        "name": "Registered Nurse (non-tech control)",
        "resume": """
Zahra Norouzi
Registered Nurse

SUMMARY
Registered nurse with 6 years of experience in emergency and critical care
units, providing patient care and coordinating with medical teams.

SKILLS
Patient assessment, emergency care, IV therapy, wound care, patient
education, electronic health records (EHR), CPR/BLS certified, team
coordination

EXPERIENCE
Senior Nurse, Milad Hospital — 2020 to Present
- Provided direct patient care in the emergency department, triaging up to
  30 patients per shift.
- Trained new nursing staff on hospital protocols and EHR systems.

Staff Nurse, Imam Khomeini Hospital — 2017 to 2020
- Administered medications and monitored patient vitals in the ICU.

EDUCATION
B.Sc. in Nursing, Tehran University of Medical Sciences — 2013-2017
""",
    },
    {
        "name": "Sales Manager (non-tech control)",
        "resume": """
Behnam Rahimi
Sales Manager

SUMMARY
Sales manager with 8 years of experience leading B2B sales teams in the
retail and consumer goods industry.

SKILLS
B2B sales, team leadership, CRM (Salesforce), negotiation, account
management, sales forecasting, market analysis, customer relationship
management

EXPERIENCE
Regional Sales Manager, a consumer goods distributor — 2019 to Present
- Managed a team of 12 sales representatives across three provinces.
- Grew regional revenue by 30% over three years through new account
  acquisition.
- Implemented Salesforce CRM to improve pipeline visibility.

Sales Representative, an FMCG company — 2015 to 2019
- Managed relationships with retail partners and negotiated annual contracts.

EDUCATION
B.A. in Business Administration, University of Tehran — 2011-2015
""",
    },
]

assert len(MOCK_RESUMES) == 20
