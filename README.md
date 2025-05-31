# LLM2Query

## 1. Statement Problem ❤️‍🩹
The medical field, particularly **cardiology**, generates an immense amount of complex and often unstructured data. Physicians spend a significant amount of time manually navigating and extracting relevant information from these datasets, which slows down the decision-making process and reduces efficiency. Rapid and intuitive access to specific data is crucial for timely diagnoses and effective treatments.

Our prototype aims to address this challenge. The goal is to minimize the time cardiologists spend retrieving relevant information from databases, allowing them to focus more on analysis and patient care. 

### 1.1 Dataset 🏥
For the development and testing of the prototype, we utilized a **real-world dataset** comprising anonymized patient information collected from various medical visits in the Campania region of Italy. This dataset, while sensitive in nature, has been crucial for training and validating our system's ability to process and query diverse medical records relevant to cardiology. The variety of visit types within the dataset ensures robust testing across different clinical scenarios.

## 2. Our Solution 💡
The objective is to democratize access to complex information contained within medical databases through a **natural language interface**.

Our solution is built upon a **modular and scalable architecture**, designed to interpret cardiologists' natural language queries and translate them into executable interrogations on a MongoDB database. In order to achieve this goal, our system leverages a sophisticated query construction engine powered by **Google's Gemini API**, combined with a **Retrieval Augmented Generation** (RAG) approach. This integration allows for highly accurate interpretation of nuanced medical queries and the generation of precise **MongoDB query language** (MQL).

![Prototype Architecture](images/LLM2Query_Architecture.png)

### 2.1 🟠 Orange Flow: Data Preprocessing and Ingestion

This flow represents the initial stage of data preparation and ingestion. 
* Raw medical data is rigorously preprocessed using PySpark for cleaning, transformation, and standardization. The refined dataset is then efficiently loaded into our MongoDB database, forming the foundation for all subsequent queries.

### 2.2 🟢 Green Flow: Documentation Embedding 
This flow describes the crucial preliminary step of preparing the system's knowledge base.

* Documentation Preparation: Separate document files detailing the schema of your dataset (table descriptions, field meanings, relationships) are prepared.
* Embedding Generation: These documentation files are processed, and their textual content is converted into numerical embeddings using the gte-large model from the Hugging Face library.
* Vector Database Storage: The generated embeddings are then stored in our ChromaDB vector database, making them readily available for efficient retrieval by the RAG component.

### 2.3 🔵 Cyan Flow: Natural Language Query Processing

This flow outlines how user natural language queries are transformed into executable MongoDB queries.

* Query Embedding & Retrieval: The user's natural language query is converted into embeddings. These embeddings are then used to retrieve the most relevant dataset descriptions (documents containing schema and data context) from our knowledge base.
* LLM Query Generation (RAG): The top three most relevant documents are provided as context to our LLM (powered by Gemini API). Leveraging a Retrieval Augmented Generation (RAG) approach, the LLM then generates a precise MongoDB query based on the user's input and the retrieved context.
* Query Validation & Execution: The generated query undergoes a validation check by our query engine before being executed on the MongoDB database to retrieve the desired results.

### 2.4 🔴 Red Flow: Pre-built Analytics and User Interaction

This flow describes how users can access and interact with pre-defined analytical views within the system.

* User Selection: Through a Streamlit interface, users can select various pre-built analytical options.
* Data Retrieval & Presentation: Based on the user's choices, the system executes specific MongoDB queries to retrieve the necessary data. This data is then visualized and presented to the user via the Streamlit interface, providing immediate insights without the need for natural language querying.

## 3. Modules Description 📦

## 4. BenchMark Test 📊
To rigorously evaluate the performance and accuracy of our LLM2Query system, we conducted a comprehensive benchmark using a set of curated natural language queries. Our primary goal was to assess the system's ability to accurately translate complex medical requests into executable MongoDB queries and retrieve the correct patient data, particularly highlighting the impact of the Retrieval Augmented Generation (RAG) approach.

### 4.1 Methodology
Our benchmark methodology is designed to provide a clear comparison between the system's output and a "gold standard" of human-generated, correct results. Wwe manually crafted the ground truth MongoDB queries and executed them against our dataset to obtain the "gold standard" result set. This represents the ideal outcome for each query.

* We compiled a test set consisting of 30 distinct natural language queries relevant to cardiological data, simulating real-world requests from physicians.
    * 10 Easy Queries
    * 10 Medium Queries
    * 10 Difficult Queriez

### 4.2 System Evaluation
* We ran each of the 30 natural language queries through our LLM2Query system under two configurations:
  * With RAG: The system leverages the Retrieval Augmented Generation approach to enrich the LLM's context for query generation.
  * Without RAG: The system relies solely on the LLM's inherent knowledge for query generation, without the additional context provided by RAG.

### 4.3 Metric Calculation
* We used a custom Python script to compare the system-generated result sets (both with and without RAG) against the gold standard result set.
* The script calculates several key metrics to quantify performance:
    * Precision: TP/(TP+FP) - Measures the proportion of relevant IDs among the retrieved IDs.
    * Recall: TP/(TP+FN) - Measures the proportion of relevant IDs that were successfully retrieved out of the total relevant IDs.
    * F1 Score: 2∗(Precision∗Recall)/(Precision+Recall) - The harmonic mean of Precision and Recall, providing a single score that balances both.
    * Jaccard Index: TP/(TP+FP+FN) - Measures the similarity between the predicted and gold standard sets.

## 5. Visual Demo 🎬

## 6. Installation guide 🛠️
This guide will walk you through the steps required to set up and run the LLM2Query prototype on your local machine. Please note that due to the sensitive nature of our primary dataset, you will need to prepare your own test data.

### 6.1 Prerequisites
Before you begin, ensure you have the following:

* Git installed.
* MongoDB Atlas Account: A free-tier cluster is sufficient. You will need your cluster's connection URI, in the website [MongoDB Atlas](https://www.mongodb.com/it-it/atlas?msockid=2ef09abe795160c13ec18e38788c61da).
* LLM API Key: An API key for Google Gemini (recommended) or any other large language model service you intend to use.

### 6.2 Setup Steps
Follow these steps to get the project up and running:

#### 6.2.1 Prepare Your Data
As our original dataset contains sensitive information, you will need to create your own for testing purposes.

* Develop a CSV file containing your trial patient data. Ensure it includes fields relevant to cardiological scenarios (e.g., patient ID, age, gender, diagnoses, lab results).
* Create a separate set of document files (e.g., text files or markdown files) that describe the schema of your dataset. Each document should detail a specific table/collection or a set of fields within your CSV, explaining their meaning and relationships. These documents will be used for Retrieval Augmented Generation (RAG).

#### 6.2.2 Configure a secret.json file
Create a file named `secret.json` in the root directory of your project. This file will store sensitive information and should not be committed to your version control (e.g., Git).

The structure should resemble the following, with your specific details:
```json
{
  "MONGO_BASE_URI": "mongodb+srv://<username>:<password>@<cluster-url>/<database-name>?retryWrites=true&w=majority",
  "GOOGLE_API_KEY": "YOUR_GEMINI_API_KEY",
  "COLLECTION_STRING_LIST":[
   "PATIENTS_DATA",
   "EVENT_LIST",
   "RECOVERY",
  ]
}
```
Replace placeholder values with your actual credentials and names.

#### 6.2.3 Preprocess Data and Generate Embeddings
Navigate to the `preprocessing` directory within the repository. You will use the provided Jupyter notebooks (preferably in a Colab environment due to computational requirements for embeddings) to prepare your data.

* Data Cleaning and MongoDB Upload Notebook:
   * Open and run the notebook dedicated to cleaning your CSV data and uploading it to your MongoDB Atlas cluster. This notebook will handle the initial data pipeline.
* Embedding Generation Notebook:
   * Open and run the notebook designed for creating embeddings from your dataset description documents. These embeddings are crucial for the RAG component to function effectively. The embeddings will be stored in your specified MongoDB collection.
   * If you generated your embeddings in a remote environment (e.g., Google Colab) and stored them in a ChromaDB instance, it's crucial to ensure your local Streamlit environment can access them. You'll need to download the ChromaDB data directory from Colab and place it in an accessible location for your local project. The Streamlit application must be configured to point to this directory.

#### 6.2.4 Set Up Pythone Enviroment and Dependencies
It's recommended to create a virtual environment to manage project dependencies.
```bash
# Clone the repository (if you haven't already)
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```
#### 6.2.5 Launch the Streamlit Application
With your data processed, embeddings in place, and environment set up, you can now launch the Streamlit interface.

```bash
# Ensure your virtual environment is activated
streamlit run app.py
```
This command will open the application in your default web browser, allowing you to interact with the medical assistant prototype.
