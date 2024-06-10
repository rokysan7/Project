from openai import OpenAI
import re
import streamlit as st
import pandas as pd

client = OpenAI(
    api_key = st.secrets['general']['openai_api_key']
)

def normalize_input(text):
    pattern = re.compile(r"(\S+)\s+(\S+)\s+(\d+)명\s+(\d+)개월")
    matches = pattern.findall(text)
    
    results = []
    for match in matches:
        product = match[0].strip(' ,')
        license = match[1].strip(' ,')
        users = match[2].strip(' ,')
        months = match[3].strip(' ,')
        results.append((product, license, users, months))
    
    return results

def answer_quote(user_input, filtered_df):
    df_str = filtered_df.to_string(index=False)
    
    PROMPT_TEMPLATE = """
    Role: 
    너는 에듀테크 제품을 retail 하는 '모노프로'라는 회사의 상담 직원이야.
    
    Instructions:
    - 너는 물건의 견적을 계산해서 알려주면 돼.
    - 견적의 내용은 Product Information을 철저하게 따르면 돼.
    - 만약 10개 이상 구입한다면, 할인이 가능하니 이메일로 요청해 달라고 말해.
    - Product Information에 없는 내용을 견적 요청 받는다면 '견적 주신 상품은 취급하지 않는 상품입니다. 저희 회사로 이메일을 남겨주시면 협의 후 납품 가능 여부를 알려드리겠습니다.' 라고 답변해야해.


    Context:
    - 항상 친절하게 모노프로 직원으로 행동해야해.
    
    견적 질문:
    {user_input}

    Product Information:
    {df_str}
    """
    
    prompt = PROMPT_TEMPLATE.format(user_input = user_input, df_str = df_str)
    
    prompt_messages = [{"role": "system", "content": prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt_messages
    )
    
    data = response.choices[0].message.content
    return data

def read_quote(user_input, df):
    
    unique_licenses = df.groupby('품명')['라이센스'].unique().reset_index()
    df_str = unique_licenses.to_string(index=False)


    PROMPT_TEMPLATE = """
    Role: 
    너는 견적서의 내용을 Format에 맞게 반환하는 프로그램이야.

    Format:
    - 품명(영어), 라이센스(영어), 유저수, 개월
    - 1개의 주문건수의 format example: chatgpt plus 1명 1개월
    - 1개 이상의 주문건수의 format example: chatgpt plus 1명 1개월, padlet gold 20명 12개월
    - 1개 이상의 주문건수의 format example: chatgpt plus 1명 1개월, padlet gold 20명 12개월, craiyon pro 1명 1개월

    Instructions:
    - 무조건 Format으로 답을 반환해야해
    - 사용자가 '품명'을 한글로 적는다면 너는 Product Information에 있는 품명(영어)으로 번역해서 말해.
    - '유저수'와 '개월수'의 default 값은 '1'이다.
    - '유저수'와 '개월수'가 없다면 default 값을 반환한다. 
    - 만약 '품명'만 존재한다면 너는 Product Information에 있는 '라이센스' 리스트의 0번쨰 인덱스 값으로 '라이센스'를 반환.
    - Product Information에 없는 내용을 견적 요청 한다면 '품명'에는 'Null', '라이센스'도 'Null'을 반환하면 돼.
    - Format 이외에 다른 대답은 절대 하지마.
    - 콤마(,)는 구분을 위해 개월 뒤에만 쓸것.
     
 
    견적 질문:
    {user_input}

    Product Information:
    {df_str}
    """
    
    prompt = PROMPT_TEMPLATE.format(user_input = user_input, df_str = df_str)
    
    prompt_messages = [{"role": "system", "content": prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt_messages
    )
    
    data = response.choices[0].message.content
    return data

def get_products_dataframe(quote, df):
    products_and_licenses = [(item[0], item[1]) for item in quote if item[0] != 'Null' and item[1] != 'Null']
    filtered_df = pd.DataFrame()
    for product, license in products_and_licenses:
        temp_df = df[(df['품명'] == product) & (df['라이센스'] == license)][['품명', '라이센스', '유저수', '개월수', '가격', '메모']]
        filtered_df = pd.concat([filtered_df, temp_df], ignore_index=True)
    return filtered_df

# user_input = "유튜브 프리미엄 3명이서 결제할건데 견적 내주."

# df = pd.read_excel('./quote.xlsx')

# print(read_quote(user_input, df))

# print(answer_quote(user_input, get_products_dataframe(normalize_input(read_quote(user_input, df)), df)))