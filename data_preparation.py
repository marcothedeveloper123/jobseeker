import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import stopwords
import functools
import logging

nltk.download("stopwords")
nltk.download("wordnet")


def handle_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

    return wrapper


@handle_error
class DataLoader:
    def __init__(self, file_path: str):
        """Initialize a DataCleaner instance."""
        if not isinstance(file_path, str):
            raise TypeError("file_path must be a string.")
        self.file_path = file_path

    @handle_error
    def load_data(self) -> pd.DataFrame:
        """Load data from a JSON file."""
        data = pd.read_json(self.file_path)
        return data


class TextProcessing:
    """Class for performing text processing on a DataFrame."""

    @handle_error
    def __init__(self, df) -> None:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input data must be a Pandas DataFrame.")
        self.df = df

    @handle_error
    def clean_text(self, df):
        """Clean the 'skills' column of the DataFrame."""
        for index, row in df.iterrows():
            skills = row["skills"]
            skill_list = skills["skills"]

            for skill in skill_list:
                name = skill["name"]

                cleaned_name = name.lower()  # Lower case
                skill["name"] = cleaned_name

                clean_re = r"[^a-z0-9\s-]"
                cleaned_name = re.sub(clean_re, "", cleaned_name)  # Remove punctuation
                skill["name"] = cleaned_name

                cleaned_name = re.sub(r"\d+", "", cleaned_name)  # Remove digits
                skill["name"] = cleaned_name

                cleaned_name = cleaned_name = " ".join(
                    word for word in cleaned_name.split() if word
                )  # Replace multiple spaces with a single space
                skill["name"] = cleaned_name

                cleaned_name = (
                    cleaned_name.strip()
                )  # Remove leading/trailing whitespace
                skill["name"] = cleaned_name

            skills["skills"] = skill_list
            self.df.at[index, "skills"] = skills
        return df

    @handle_error
    def clean(self, df):
        """Perform full data cleaning by calling individual cleaning functions like clean_text()."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input data must be a Pandas DataFrame.")
        cleaned_df = self.clean_text(df)
        return cleaned_df

    @handle_error
    def prepare_columns(self, df):
        """Enrich the DataFrame by preparing and adding columns."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input data must be a Pandas DataFrame.")
        cleaned_df = self.clean(df)
        cleaned_df = self._extract_names(cleaned_df)
        cleaned_df = self._count_phrases(cleaned_df)
        cleaned_df = self._create_skills_string(cleaned_df)
        cleaned_df = self._split_into_words(cleaned_df)
        cleaned_df = self._count_uniques(cleaned_df)
        return cleaned_df

    @handle_error
    def _extract_names(self, df):
        """Extract skill names from nested structures."""
        df["skills"] = df["skills"].apply(
            lambda x: [skill["name"] for skill in x["skills"]]
        )
        return df

    def _count_phrases(self, df):
        """Count the number of phrases in the skills column."""
        df["num_phrases"] = df["skills"].str.len()
        return df

    @handle_error
    def _create_skills_string(self, df):
        """Join skills into a single text string."""
        df["skills_text"] = df["skills"].apply(" ".join)
        return df

    @handle_error
    def _split_into_words(self, df):
        """Split skills_text into individual words."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input data must be a Pandas DataFrame.")
        df["temp_words"] = df["skills_text"].apply(word_tokenize)
        df["num_words"] = df["temp_words"].str.len()
        df["unique_words"] = df["temp_words"].apply(lambda x: " ".join(set(x)))
        del df["temp_words"]
        return df

    @handle_error
    def _count_uniques(self, df):
        """Count the number of unique words per row."""
        df["num_uniques"] = df["unique_words"].apply(lambda x: len(x.split()))
        return df

    @handle_error
    def get_prepared_df(self) -> pd.DataFrame:
        """Return the prepared DataFrame."""
        prepared_df = self.prepare_columns(self.df)
        return prepared_df


class SkillDataProcessor:
    """Class for processing skills data."""

    @handle_error
    def __init__(self, data: pd.DataFrame):
        """Initialize a SkillCleaner instance."""
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a Pandas DataFrame.")
        super().__init__()
        self.data = data
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()

    def filter_stops(self, series: pd.Series) -> pd.Series:
        """Remove stopwords from a Pandas Series containing text."""
        return series.apply(
            lambda x: " ".join(
                [word for word in x.split() if word not in self.stop_words]
            )
        )

    def lemmatize_words(self, series: pd.Series) -> pd.Series:
        """Lemmatize words in a Pandas Series using NLTK's WordNetLemmatizer."""

        def lemmatize_text(text):
            # Lemmatize the entire text as a single string
            return " ".join(self.lemmatizer.lemmatize(word) for word in text.split())

        # Apply lemmatization to each row in the series
        return series.apply(lemmatize_text)

    def normalize_and_encode_ascii(self, series: pd.Series) -> pd.Series:
        """Normalize and encode text to ASCII."""
        return (
            series.str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
        )


def calculate_tfidf_scores(dataframe, text_column="unique_words", max_features=50):
    """
    Calculate TF-IDF scores for a given text column in a dataframe.
    """
    # Initialize SkillDataProcessor and process the dataframe
    skill_processor = SkillDataProcessor(dataframe)
    processed_dataframe = skill_processor.filter_stops(dataframe[text_column])
    processed_dataframe = skill_processor.lemmatize_words(processed_dataframe)
    processed_dataframe = skill_processor.normalize_and_encode_ascii(
        processed_dataframe
    )
    # Extract the text data from the specified column
    documents = processed_dataframe.tolist()
    # Create a TF-IDF vectorizer with a specified maximum number of features and remove stopwords
    tfidf_vectorizer = TfidfVectorizer(max_features=max_features)
    # Create TF-IDF matrix
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    # Create a dataframe with TF-IDF scores and term names
    tfidf_scores = pd.DataFrame(
        tfidf_matrix.toarray(), columns=tfidf_vectorizer.get_feature_names_out()
    )
    return tfidf_scores
