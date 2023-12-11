import pandas as pd
import json


def prepare_data():
    # Load data from the JSON file and create a DataFrame
    file_path = (
        r"data/silver/head_of_product/skills_json_from_df_head_of_product_v4.json"
    )

    with open(file_path, "r") as file:
        data = json.load(file)

        df = pd.DataFrame(data)

        # Clean skills column by extracting names
        df["skills"] = df["skills"].apply(
            lambda x: [skill["name"] for skill in x["skills"]]
        )

        # Count number of phrases inside skills
        df["num_phrases"] = df["skills"].str.len()

        # Join skills into full text string
        df["skills_text"] = df["skills"].apply(" ".join)

        # Split skills into individual words
        words = df["skills_text"].str.split(None)

        # Count number of words
        df["num_words"] = words.str.len()

        # Get unique words per row
        df["unique_words"] = words.apply(set)
        df["unique_words"] = df["unique_words"].apply(list)

        # Count uniques and summarize
        df["num_uniques"] = df["unique_words"].apply(len)
        # word_counts = df.groupby("job_title")["num_uniques"].sum()

    return df
