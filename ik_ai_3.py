import tkinter as tk
from tkinter import messagebox
import json
from groq import Groq
import random
import ast


# Anahtar kelime-kategori json dosyaları
kategori_dosyalari = {
    "caliskanlik": "caliskanlik.json",
    "durustluk": "durustluk.json",
    "sadakat": "sadakat.json",
    "stres_yonetimi": "stres_yonetimi.json",
    "takim_calismasi": "takim_calismasi.json",
    "teknik": "teknik.json",
    "uyumluluk": "uyumluluk.json"
}

kategori_verileri = {}
for kategori, dosya in kategori_dosyalari.items():
    with open(dosya, "r", encoding="utf-8") as f:
        kategori_verileri[kategori] = json.load(f)

# Groq API client
client = Groq(api_key="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")

# Ana system prompt
system_prompt = {
    "role": "system",
    "content": """You are an HR analysis assistant. You speak Turkish. Your task is to analyze a given employee description and identify which traits from a fixed set of keywords apply to that person.
Your keyword pool is:
(teknik, uyumlu, sadakat, durustluk, stres_yonetimi, takim_calismasi, uyumluluk, caliskanlik)
Carefully read the description and extract only the keywords that match the described personality or skills. Include both direct matches and implied traits (e.g., "calm under pressure" implies "stres_yonetimi").
Your output should be a clean Python-style list for example ["teknik","durustluk"], all in lowercase, containing only the matched keywords. Do not include any explanations or extra text."""
}

# Case study system prompt
case_system_prompt = {
    "role": "system",
    "content": """
You are a professional HR content generator AI that specializes in creating realistic case studies and evaluation materials for interviews. Your task is to generate one case-based interview question and its ideal answer, based on two given competency categories.

The categories can include traits such as:
(teknik, uyumlu, sadakat, dürüstlük, stres_yönetimi, takım_çalışması, uyumluluk, çalışkanlık)

Instructions:
- Create a realistic workplace scenario that reflects both of the given traits.
- Based on that scenario, write one interview question designed to assess the candidate’s behavior or skill.
- Provide a model answer that fully demonstrates the ideal response.
- Return your output only as a Python-style list, in the following format:
  ["interview_question_here", "ideal_answer_here"]

Use Turkish in both the question and the answer.
Do not include any commentary, explanation, or text outside the list.
"""
}

# Yardımcı fonksiyonlar
def temizle_ve_donustur(girdi):
    try:
        if isinstance(girdi, str):
            return ast.literal_eval(girdi)
        elif isinstance(girdi, list):
            return girdi
        else:
            raise ValueError("Beklenmeyen format")
    except Exception:
        girdi = girdi.replace("[", "").replace("]", "")
        ogeler = [x.strip().strip("'\"") for x in girdi.split(",")]
        return ogeler


# Tkinter uygulaması
class InterviewApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Mülakat Asistanı")
        self.toplam_puan = 0
        self.liste_kat = []
        self.init_ui()

    def init_ui(self):
        tk.Label(self.master, text="Personel tanımını girin:").pack()
        self.input_entry = tk.Entry(self.master, width=80)
        self.input_entry.pack(pady=5)

        tk.Button(self.master, text="Başlat", command=self.process_input).pack(pady=5)

        self.output_text = tk.Text(self.master, height=20, width=80)
        self.output_text.pack(pady=10)

    def process_input(self):
        user_input = self.input_entry.get()
        if not user_input:
            messagebox.showwarning("Uyarı", "Lütfen bir açıklama girin.")
            return

        chat_history = [system_prompt, {"role": "user", "content": user_input}]
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=chat_history,
            max_tokens=150,
            temperature=1.0
        )
        assistant_reply = response.choices[0].message.content
        self.liste_kat = temizle_ve_donustur(assistant_reply)
        self.output_text.insert(tk.END, f"Belirlenen kategoriler: {self.liste_kat}\n\n")

        self.ask_questions_for_categories()

    def ask_questions_for_categories(self):
        for kategori in self.liste_kat:
            if kategori not in kategori_verileri:
                continue
            self.ask_question(kategori_verileri[kategori], kategori)

        if len(self.liste_kat) >= 2:
            self.case_study_sorusu_ve_puanla(self.liste_kat[0], self.liste_kat[1])

        self.output_text.insert(tk.END, f"\nToplam Nihai Puanınız: {self.toplam_puan}")

    def ask_question(self, grup, kategori):
        alt_toplam = 0
        sayilar = random.sample(range(0, len(grup)), 3)
        for sayi in sayilar:
            soru = grup[sayi]["question"]
            cevap = grup[sayi]["answer"]
            aday_cevap = self.get_user_answer(soru)
            puan = self.evaluate_answer(soru, cevap, aday_cevap)
            self.output_text.insert(tk.END, f"Soru: {soru}\nModel Cevap: {cevap}\nVerdiğiniz Puan: {puan}\n\n")
            self.toplam_puan += puan

    def get_user_answer(self, soru):
        popup = tk.Toplevel(self.master)
        popup.title("Soru")
        tk.Label(popup, text=soru, wraplength=400).pack(pady=5)
        cevap_entry = tk.Text(popup, height=4, width=50)
        cevap_entry.pack(pady=5)
        cevap = {"text": ""}

        def on_submit():
            cevap["text"] = cevap_entry.get("1.0", tk.END).strip()
            popup.destroy()

        tk.Button(popup, text="Cevabı Gönder", command=on_submit).pack(pady=5)
        self.master.wait_window(popup)
        return cevap["text"]

    def evaluate_answer(self, soru, ideal_cevap, aday_cevap):
        eval_prompt = {
            "role": "system",
            "content": """You are an interview evaluator AI. Compare the applicant’s answer with the model answer and give a score from 1 to 10. Only return the score as a number."""
        }
        chat = [eval_prompt, {"role": "user", "content": f"""
        Question: "{soru}"
        Real Answer: "{ideal_cevap}"
        Candidate Answer: "{aday_cevap}"
        """}]
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=chat,
            max_tokens=50,
            temperature=1.0
        )
        return int(response.choices[0].message.content.strip())

    def case_study_sorusu_ve_puanla(self, kategori1, kategori2):
        prompt_text = f"""Lütfen "{kategori1}" ve "{kategori2}" kategorilerine uygun bir işyeri vaka senaryosu oluştur. 
Bu senaryoya dayanarak bir mülakat sorusu ve örnek bir cevap üret. 
Cevabını sadece şu formatta döndür: ["soru", "cevap"]"""

        chat_history = [case_system_prompt, {"role": "user", "content": prompt_text}]
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=chat_history,
            max_tokens=200,
            temperature=1.0
        )
        case_reply = ast.literal_eval(response.choices[0].message.content)
        soru, ideal_cevap = case_reply
        aday_cevap = self.get_user_answer(soru)
        puan = self.evaluate_answer(soru, ideal_cevap, aday_cevap)
        self.output_text.insert(tk.END, f"\n[CASE STUDY]\nSoru: {soru}\nModel Cevap: {ideal_cevap}\nVerdiğiniz Puan: {puan}\n")
        self.toplam_puan += puan


# Uygulama başlatılıyor
root = tk.Tk()
app = InterviewApp(root)
root.mainloop()
