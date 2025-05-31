# LLM2Query

## Statement Problem
The medical field, particularly cardiology, generates an immense amount of complex and often unstructured data. Physicians spend a significant amount of time manually navigating and extracting relevant information from these datasets, which slows down the decision-making process and reduces efficiency. Rapid and intuitive access to specific data is crucial for timely diagnoses and effective treatments.

Our prototype aims to address this challenge. The goal is to minimize the time cardiologists spend retrieving relevant information from databases, allowing them to focus more on analysis and patient care. 

### Dataset
For the development and testing of the prototype, we utilized a real-world dataset comprising anonymized patient information collected from various medical visits in the Campania region of Italy. This dataset, while sensitive in nature, has been crucial for training and validating our system's ability to process and query diverse medical records relevant to cardiology. The variety of visit types within the dataset ensures robust testing across different clinical scenarios.

## Our Solution 
The objective is to democratize access to complex information contained within medical databases through a natural language interface.

Our solution is built upon a modular and scalable architecture, designed to interpret cardiologists' natural language queries and translate them into executable interrogations on a MongoDB database. In order to achieve this goal, our system leverages a sophisticated query construction engine powered by Google's Gemini API, combined with a Retrieval Augmented Generation (RAG) approach. This integration allows for highly accurate interpretation of nuanced medical queries and the generation of precise MongoDB query language (MQL).

