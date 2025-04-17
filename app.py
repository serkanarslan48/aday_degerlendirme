import streamlit as st
from sentence_transformers import SentenceTransformer, util
import torch
import json
from groq import Groq
import random
import ast

model = SentenceTransformer('all-MiniLM-L6-v2')

file_path1 = "caliskanlik.json"
with open(file_path1, "r", encoding="utf-8") as f:
    caliskanlik_json = json.load(f)

file_path2 = "durustluk.json"
with open(file_path2, "r", encoding="utf-8") as f:
    durustluk_json = json.load(f)

file_path3 = "sadakat.json"
with open(file_path3, "r", encoding="utf-8") as f:
    sadakat_json = json.load(f)

file_path4 = "stres_yonetimi.json"
with open(file_path4, "r", encoding="utf-8") as f:
    stres_json = json.load(f)

file_path5 = "takim_calismasi.json"
with open(file_path5, "r", encoding="utf-8") as f:
    takim_json = json.load(f)

file_path6 = "teknik.json"
with open(file_path6, "r", encoding="utf-8") as f:
    teknik_json = json.load(f)

file_path7 = "uyumluluk.json"
with open(file_path7, "r", encoding="utf-8") as f:
    uyumluluk_json = json.load(f)

liste1 = [caliskanlik_json, durustluk_json, sadakat_json, stres_json, takim_json, teknik_json, uyumluluk_json]
toplam_puan = 0

kategori_isimleri = {
    "teknik": teknik_json,
    "uyumlu": uyumluluk_json,
    "sadakat": sadakat_json,
    "durustluk": durustluk_json,
    "stres_yonetimi": stres_json,
    "takim_calismasi": takim_json,
    "uyumluluk": uyumluluk_json,
    "caliskanlik": caliskanlik_json
}

def temizle_ve_donustur(girdi):
    try:
        # Eğer model düzgün bir string döndürdüyse doğrudan dönüştür
        if isinstance(girdi, str):
            return ast.literal_eval(girdi)
        # Zaten liste ise dokunma
        elif isinstance(girdi, list):
            return girdi
        else:
            raise ValueError("Beklenmeyen format")
    except Exception:
        # Elle düzeltme: tırnak yoksa vs.
        girdi = girdi.replace("[", "").replace("]", "")
        ogeler = [x.strip().strip("'\"") for x in girdi.split(",")]
        return ogeler

client = Groq(api_key="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")

system_prompt = {
    "role": "system",
    "content": """You are an HR analysis assistant. You speak Turkish. Your task is to analyze a given employee description and identify which traits from a fixed set of keywords apply to that person.
Your keyword pool is:
(teknik, uyumlu, sadakat, durustluk, stres_yonetimi, takim_calismasi, uyumluluk, caliskanlik)
Carefully read the description and extract only the keywords that match the described personality or skills. Include both direct matches and implied traits (e.g., "calm under pressure" implies "stress_management"). 
Your output should be a **clean Python-style list** for example ["teknik","durustluk"], all in lowercase, containing only the matched keywords. Do not include any explanations or extra text."""}

print("Geodesic Dome Asistanına hoş geldiniz. Çıkmak için 'çık' yazabilirsiniz.\n")

# Streamlit Formu
st.title("Personel Değerlendirme Asistanı")

with st.form(key='personel_form'):
    user_question = st.text_input("Personeli Tanımlayın")
    submit_button = st.form_submit_button("Gönder")

    if submit_button and user_question:
        def sorulari_baslat(user_question):
            chat_history = [system_prompt]

            llm_prompt = f"""
            {user_question}
            """

            chat_history.append({"role": "user", "content": llm_prompt})

            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=chat_history,
                max_tokens=150,
                temperature=1.0
            )

            assistant_reply = response.choices[0].message.content
            liste_kat = temizle_ve_donustur(assistant_reply)
            st.write(f"Belirlenen Kategoriler: {liste_kat}")

            for i in liste_kat:
                grup = kategori_isimleri[i]
                for k in range(2):  # Her kategori için iki soru alalım
                    st.write(f"**Soru:** {grup[k]['question']}")
                    candidate_answer = st.text_input(f"Cevabınız ({grup[k]['question']}):", key=f"{i}_{k}")

                    if candidate_answer:
                        llm_prompt1 = f"""
                            You are an expert interview evaluator for a food company's quality department. Your job is to score the applicant's answer based on how well it matches the model answer. 
                            Give a score from 1 to 10 using the following criteria:
                            - 10: Excellent — very accurate, complete, and nearly identical in meaning and depth to the real answer.
                            - 7–9: Good — mostly correct with minor gaps or slight inaccuracies.
                            - 4–6: Average — partially correct but missing some important points.
                            - 1–3: Poor — mostly incorrect, irrelevant, or very incomplete.

                            Only return the score as a number. Do not explain your reasoning.

                            Question: "{grup[k]['question']}"
                            Real Answer: "{grup[k]['answer']}"
                            Candidate Answer: "{candidate_answer}"
                        """

                        chat_history1 = [{"role": "system", "content": "You are an interview evaluator AI for a food company."}]
                        chat_history1.append({"role": "user", "content": llm_prompt1})

                        response1 = client.chat.completions.create(
                            model="llama3-70b-8192",
                            messages=chat_history1,
                            max_tokens=150,
                            temperature=1.0)

                        st.write(f"Model Cevabı: {grup[k]['answer']}")
                        st.write(f"Puanınız: {response1.choices[0].message.content}")
            st.write(f"Toplam Puan {toplam_puan}")


        sorulari_baslat(user_question)
