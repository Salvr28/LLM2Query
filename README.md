# LLM2Query

## 1. Statement Problem
The medical field, particularly **cardiology**, generates an immense amount of complex and often unstructured data. Physicians spend a significant amount of time manually navigating and extracting relevant information from these datasets, which slows down the decision-making process and reduces efficiency. Rapid and intuitive access to specific data is crucial for timely diagnoses and effective treatments.

Our prototype aims to address this challenge. The goal is to minimize the time cardiologists spend retrieving relevant information from databases, allowing them to focus more on analysis and patient care. 

### 1.1 Dataset
For the development and testing of the prototype, we utilized a **real-world dataset** comprising anonymized patient information collected from various medical visits in the Campania region of Italy. This dataset, while sensitive in nature, has been crucial for training and validating our system's ability to process and query diverse medical records relevant to cardiology. The variety of visit types within the dataset ensures robust testing across different clinical scenarios.

## 2. Our Solution 
The objective is to democratize access to complex information contained within medical databases through a **natural language interface**.

Our solution is built upon a **modular and scalable architecture**, designed to interpret cardiologists' natural language queries and translate them into executable interrogations on a MongoDB database. In order to achieve this goal, our system leverages a sophisticated query construction engine powered by **Google's Gemini API**, combined with a **Retrieval Augmented Generation** (RAG) approach. This integration allows for highly accurate interpretation of nuanced medical queries and the generation of precise **MongoDB query language** (MQL).

![Prototype Architecture](images/LLM2Query_Architecture.png)

### 2.1 🟠 Orange Flow: Data Preprocessing and Ingestion

This flow represents the initial stage of data preparation and ingestion. Raw medical data is rigorously preprocessed using PySpark for cleaning, transformation, and standardization. The refined dataset is then efficiently loaded into our MongoDB database, forming the foundation for all subsequent queries.

### 2.2 🔵 Cyan Flow: Natural Language Query Processing

This flow outlines how user natural language queries are transformed into executable MongoDB queries.

* Query Embedding & Retrieval: The user's natural language query is converted into embeddings. These embeddings are then used to retrieve the most relevant dataset descriptions (documents containing schema and data context) from our knowledge base.
* LLM Query Generation (RAG): The top three most relevant documents are provided as context to our LLM (powered by Gemini API). Leveraging a Retrieval Augmented Generation (RAG) approach, the LLM then generates a precise MongoDB query based on the user's input and the retrieved context.
* Query Validation & Execution: The generated query undergoes a validation check by our query engine before being executed on the MongoDB database to retrieve the desired results.

### 2.3 🔴 Red Flow: Pre-built Analytics and User Interaction

This flow describes how users can access and interact with pre-defined analytical views within the system.

* User Selection: Through a Streamlit interface, users can select various pre-built analytical options.
* Data Retrieval & Presentation: Based on the user's choices, the system executes specific MongoDB queries to retrieve the necessary data. This data is then visualized and presented to the user via the Streamlit interface, providing immediate insights without the need for natural language querying.

## 3. Modules

## 4. BenchMark Test
To rigorously evaluate the performance and accuracy of our LLM2Query system, we conducted a comprehensive benchmark using a set of curated natural language queries. Our primary goal was to assess the system's ability to accurately translate complex medical requests into executable MongoDB queries and retrieve the correct patient data, particularly highlighting the impact of the Retrieval Augmented Generation (RAG) approach.

### 3.1 Methodology
Our benchmark methodology is designed to provide a clear comparison between the system's output and a "gold standard" of human-generated, correct results. Wwe manually crafted the ground truth MongoDB queries and executed them against our dataset to obtain the "gold standard" result set. This represents the ideal outcome for each query.

* We compiled a test set consisting of 30 distinct natural language queries relevant to cardiological data, simulating real-world requests from physicians.
    * 10 Easy Queries
    * 10 Medium Queries
    * 10 Difficult Queriez

### 3.2 System Evaluation
* We ran each of the 30 natural language queries through our LLM2Query system under two configurations:
  * With RAG: The system leverages the Retrieval Augmented Generation approach to enrich the LLM's context for query generation.
  * Without RAG: The system relies solely on the LLM's inherent knowledge for query generation, without the additional context provided by RAG.

### 3.3 Metric Calculation
* We used a custom Python script to compare the system-generated result sets (both with and without RAG) against the gold standard result set.
* The script calculates several key metrics to quantify performance:
    * Precision: TP/(TP+FP) - Measures the proportion of relevant IDs among the retrieved IDs.
    * Recall: TP/(TP+FN) - Measures the proportion of relevant IDs that were successfully retrieved out of the total relevant IDs.
    * F1 Score: 2∗(Precision∗Recall)/(Precision+Recall) - The harmonic mean of Precision and Recall, providing a single score that balances both.
    * Jaccard Index: TP/(TP+FP+FN) - Measures the similarity between the predicted and gold standard sets.
