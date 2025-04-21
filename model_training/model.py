#!/usr/bin/env python
# coding: utf-8

# In[5]:


import pandas as pd
from sklearn.preprocessing import OneHotEncoder


# In[4]:


df = pd.read_csv(r"C:\Users\Maitrayee Budhale\OneDrive\Desktop\skincare.csv")
df
df.columns


# In[6]:


# apply one hot encoding using in built function to product_type
product_type_encoded = pd.get_dummies(df, columns=['product_type'], drop_first=False)
product_type_encoded.head()


# In[7]:


# perform one hot encoding on skintypes using usesr defined function
main_skin_types = ['Sensitive', 'Combination', 'Oily', 'Dry', 'Normal']
for skin in main_skin_types:
    df[skin] = df['skintype'].apply(lambda x: 1 if skin in x else 0)
df.head()


# In[8]:


print(df.shape, product_type_encoded.shape)
# Check for overlapping column names
common_cols = set(df.columns).intersection(set(product_type_encoded.columns))
print(common_cols)

product_type_encoded.drop(columns=common_cols, errors='ignore', inplace=True)


# In[9]:


print(df.shape, product_type_encoded.shape)
# Check for overlapping column names
common_cols = set(df.columns).intersection(set(product_type_encoded.columns))
print(common_cols)

product_type_encoded.drop(columns=common_cols, errors='ignore', inplace=True)


# In[11]:


# Concatenate encoded columns with the original dataset
df_encoded = pd.concat([df, product_type_encoded], axis=1)
df_encoded.head()


# In[12]:


# Convert boolean columns to integers
product_type_cols = [col for col in df_encoded.columns if 'product_type_' in col]
df_encoded[product_type_cols] = df_encoded[product_type_cols].astype(int)
df_encoded.head()


# In[13]:


features_to_drop = ['product_name', 'product_href', 'picture_src', 'description', 'brand', 'skintype', 'notable_effects','product_type','price']
df_final = df_encoded.drop(columns=features_to_drop, errors='ignore')
df_final.head()
df_final.columns


# In[14]:


from sklearn.feature_extraction.text import TfidfVectorizer
# create object
tfidf = TfidfVectorizer()

# get tf-df values
tfidf_matrix = tfidf.fit_transform(df_encoded['notable_effects'])

# Convert to DataFrame
tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=tfidf.get_feature_names_out(), index=df_encoded.index)
tfidf_df
tfidf_df.columns


# In[15]:


# Concatenate all feature matrices
feature_matrix = pd.concat([tfidf_df,df_final], axis=1)
feature_matrix
feature_matrix.head()


# In[16]:


feature_matrix.columns


# In[17]:


from sklearn.metrics.pairwise import cosine_similarity
cosine_sim=cosine_similarity(feature_matrix)
cosine_sim_df = pd.DataFrame(cosine_sim, index=df['product_name'], columns=df['product_name'])
cosine_sim_df.head()


# In[18]:


from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Check similarity matrix
similarity_matrix = cosine_similarity(feature_matrix)
print(np.isnan(similarity_matrix).sum())


# In[19]:


import pandas as pd

def get_recommendations(user_skin_type, user_concern, product_category, k):
    # Map product category to the appropriate one-hot encoded column
    product_category_term = 'product_type_' + product_category
    print(user_skin_type)
    print(user_concern)
    print(product_category_term)
    
    available_terms = feature_matrix.columns.tolist()
    if user_skin_type not in available_terms or product_category_term not in available_terms:
        print("Warning: Skin type or product category term not found in feature matrix.")
        return pd.DataFrame()
        
    filtered_indices = feature_matrix[
        (feature_matrix[user_skin_type] > 0) & 
        (feature_matrix[product_category_term] > 0)
    ].index
    # Now get the corresponding rows from df_encoded using filtered indices
    filtered_data = df_encoded.loc[filtered_indices]
    
    if filtered_data.empty:
        print("No matching products found after filtering.")

    if 'notable_effects' not in filtered_data.columns:
        return pd.DataFrame()
    product_names = filtered_data['product_name'].tolist()
    # print(product_names)

    if not product_names:
        # print("No products found matching the criteria.")
        return pd.DataFrame()

     # Convert to string to avoid mismatches
    product_names = [str(name) for name in product_names]
    if 'cosine_sim_df' not in locals():
        cosine_sim = cosine_similarity(feature_matrix)
        cosine_sim_df = pd.DataFrame(cosine_sim, index=df_encoded['product_name'], columns=df_encoded['product_name'])

    cosine_sim_df = cosine_sim_df[~cosine_sim_df.index.duplicated(keep='first')]

    cosine_sim_df.index = cosine_sim_df.index.astype(str)

    mismatched_names = [name for name in product_names if name not in cosine_sim_df.index]
    cosine_sim_df.reset_index(drop=True, inplace=True)

# Convert index to string to avoid mismatch
    cosine_sim_df.index = cosine_sim_df.index.astype(str)
    # print("Number of duplicate indices after cleanup:", cosine_sim_df.index.duplicated().sum())


    # Reindex safely after cleanup
    cosine_sim_df.index = df['product_name'][~df['product_name'].duplicated(keep='first')]

    try:
        print("Cosine sim df index before reindex", cosine_sim_df.index.tolist()[:10])
        print("product names before reindex", product_names[:10])
        sim_scores = cosine_sim_df.reindex(index=product_names).mean(axis=1).sort_values(ascending=False)
        print("Top 5 Similarity Scores:\n", sim_scores.head())
    except Exception as e:
        print(f"Error after reindexing: {e}")

    top_products = sim_scores.head(k).index.tolist()
     
    df.index = df.index.astype(str)
    # Convert top_products to strings, lowercase, and strip whitespace
    top_products = [str(product).strip().lower() for product in top_products]
    print(f"df.index data type: {type(df.index[0])}")
    print(f"top_products element data type: {type(top_products[0])}")
    print("top_products:", top_products)
    print("df['product_name'] sample:", df['product_name'][:10].tolist())

    top_products = [str(item).strip().lower() for item in top_products]
    top_products_cleaned = [str(item).strip().lower() for item in top_products]
    df_cleaned = df.copy() #create copy

    # Clean the product name column of the copy
    df_cleaned['product_name'] = df_cleaned['product_name'].str.strip().str.lower()
    for product in top_products:
        if product in df_cleaned['product_name'].tolist():
            print(f"'{product}' found in df['product_name']")
        else:
            print(f"'{product}' NOT found in df['product_name']")

    # Correct way to filter using 'product_name' column, use the cleaned dataframe
    recommendations = df_cleaned[df_cleaned['product_name'].isin(top_products_cleaned)].copy()
    recommendations = recommendations.reset_index(drop=True)

    return recommendations


# In[20]:


# Get recommendations based on user input
rec=get_recommendations('Sensitive', 'Anti', 'Toner', k=5)
print(rec)


# In[21]:


rec

