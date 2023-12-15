import pandas as pd
import json
from sklearn.feature_extraction.text import TfidfVectorizer


def prepare_data():
    """
    Load data from a JSON file, clean the skills column, and create additional columns.

    Returns:
    - pd.DataFrame
        A dataframe containing the prepared data.
    """

    # Specify the file path for the JSON data
    file_path = (
        r"data/silver/head_of_product/skills_json_from_df_head_of_product_v4.json"
    )

    # Load data from the JSON file
    with open(file_path, "r") as file:
        data = json.load(file)

        # Create a DataFrame from the loaded data
        df = pd.DataFrame(data)

        # Clean the skills column by extracting names
        df["skills"] = df["skills"].apply(
            lambda x: [skill["name"] for skill in x["skills"]]
        )

        # Count the number of phrases inside skills
        df["num_phrases"] = df["skills"].str.len()

        # Join skills into a full text string
        df["skills_text"] = df["skills"].apply(" ".join)

        # Split skills into individual words
        words = df["skills_text"].str.split(None)

        # Count the number of words
        df["num_words"] = words.str.len()

        # Get unique words per row
        df["unique_words"] = words.apply(set)
        df["unique_words"] = df["unique_words"].apply(list)

        # Count uniques and summarize
        df["num_uniques"] = df["unique_words"].apply(len)
        # word_counts = df.groupby("job_title")["num_uniques"].sum()

    return df


def calculate_tfidf_scores(dataframe, text_column="skills_text", max_features=50):
    """
    Calculate TF-IDF scores for a given text column in a dataframe.

    Parameters:
    - dataframe: pd.DataFrame
        The dataframe containing the text data.
    - text_column: str, default='skills_text'
        The column name containing the text data.
    - max_features: int, default=50
        The maximum number of features (terms) to include in the TF-IDF matrix.

    Returns:
    - pd.DataFrame
        A dataframe containing TF-IDF scores for each term.
    """

    # Extract the text data from the specified column
    corpus = dataframe[text_column].astype(str).tolist()

    # Create a TF-IDF vectorizer with a specified maximum number of features
    tfidf_vectorizer = TfidfVectorizer(max_features=max_features)

    # Create TF-IDF matrix
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)

    # Create a dataframe with TF-IDF scores and term names
    tfidf_scores = pd.DataFrame(
        tfidf_matrix.toarray(), columns=tfidf_vectorizer.get_feature_names_out()
    )

    return tfidf_scores
