import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

sources = ['https://www.dawn.com/', 'https://www.bbc.com/']

def extract(source):
    # Function to scrape links, titles, and descriptions
    def scrape_website(url):
        # Initialize webdriver
        driver = webdriver.Chrome()  # You need to provide the path to your WebDriver
        
        # Open the URL
        driver.get(url)
        
        # Extract links
        links = [link.get_attribute('href') for link in driver.find_elements(By.TAG_NAME, 'a')]
        
        # Extract titles and descriptions from articles
        articles = driver.find_elements(By.TAG_NAME, 'article')
        articles_data = []
        for article in articles:
            title = article.find_element(By.TAG_NAME, 'h3').text.strip()
            description = article.find_element(By.TAG_NAME, 'p').text.strip()
            articles_data.append({'title': title, 'description': description})
        
        # Close the webdriver
        driver.quit()
        
        return links, articles_data

    # Function to save data to CSV
    def save_to_csv(data, filename):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

    # Example usage
    links, articles = scrape_website(source)
    save_to_csv(articles, f'{source.split("//")[1].split(".")[0]}_articles.csv')

def transform(source):
    # Load the data from CSV
    df = pd.read_csv(f'{source.split("//")[1].split(".")[0]}_articles.csv')

    # Perform transformation
    df['title_length'] = df['title'].apply(len)
    df['description_length'] = df['description'].apply(len)

    # Save the transformed data back to CSV
    df.to_csv(f'{source.split("//")[1].split(".")[0]}_transformed.csv', index=False)

    print(f"Transformation completed for {source}.")

def load(source):
    # Load the transformed data from CSV
    df = pd.read_csv(f'{source.split("//")[1].split(".")[0]}_transformed.csv')

    # Insert data into database (not implemented)
    print(f"Loading data from {source}:")
    print(df.head())
    print(f"Data loading completed for {source}.")

default_args = {
    'owner': 'airflow-demo',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 13),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

dag = DAG(
    'mlops-dag',
    default_args=default_args,
    description='A simple DAG for web scraping, transformation, and loading tasks',
    schedule_interval='@daily',
)

for source in sources:
    task_extract = PythonOperator(
        task_id=f'extract_{source.split("//")[1].split(".")[0]}',
        python_callable=extract,
        op_kwargs={'source': source},
        dag=dag,
    )

    task_transform = PythonOperator(
        task_id=f'transform_{source.split("//")[1].split(".")[0]}',
        python_callable=transform,
        op_kwargs={'source': source},
        dag=dag,
    )

    task_load = PythonOperator(
        task_id=f'load_{source.split("//")[1].split(".")[0]}',
        python_callable=load,
        op_kwargs={'source': source},
        dag=dag,
    )

    task_extract >> task_transform >> task_load
