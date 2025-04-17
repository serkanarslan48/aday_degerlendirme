import tkinter as tk
from tkinter import messagebox
from groq import Groq
import json
import random
import ast

client = Groq(api_key="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")

kategori_isimleri = {
    "teknik": "teknik.json",
    "uyumlu": "uyumluluk.json",
    "sadakat": "sadakat.json",
    "durustluk": "durustluk.json",
    "stres_yonetimi": "stres_yonetimi.json",
    "takim_calismasi": "takim_calismasi.json",
    "uyumluluk": "uyumluluk.json",
    "caliskanlik": "caliskanlik.json"
}

def temizle_ve_donustur(girdi):
    try:
        if isinstance(girdi, str):
            return ast.literal_eval(girdi)
        elif isinstance(girdi, list):
            return girdi
    except Exception:
        girdi = girdi.replace("[", "").replace("]", "")
        ogeler = [x.strip().strip("'\"") for x in girdi.split(",")]
        return ogeler


class InterviewApp:
    def _init_(self, master):
        self.master = master
        master.title("Mülakat Değerlendirici")

        self.label = tk.Label(master, text="Personel tanımını giriniz:")
        self.label.pack(pady=5)

        self.textbox = tk.Text(master, height=5, width=50)
        self.textbox.pack(pady=5)

        self.start_button = tk.Button(master, text="Analizi Başlat", command=self.baslat)
        self.start_button.pack(pady=10)

        self.output_text = tk.Text(master, height=15, width=60)
        self.output_text.pack(pady=10)

    def baslat(self):
        personel_tanimi = self.textbox.get("1.0", tk.END).strip()

        if not personel_tanimi:
            messagebox.showwarning("Uyarı", "Lütfen bir personel tanımı girin.")
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Anahtar kelimeler analiz ediliyor...\n")

        system_prompt = {
            "role": "system",
            "content": """You are an HR analysis assistant. You speak Turkish. Your task is to analyze a given employee description and identify which traits from a fixed set of keywords apply to that person.
            Your keyword pool is:
            (teknik, uyumlu, sadakat, durustluk, stres_yonetimi, takim_calismasi, uyumluluk, caliskanlik)
            Carefully read the description and extract only the keywords that match the described personality or skills. Include both direct matches and implied traits.
            Output must be: ["keyword1", "keyword2"] format. Do not include any explanation."""
        }

        chat_history = [system_prompt, {"role": "user", "content": personel_tanimi}]

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=chat_history,
            max_tokens=100,
            temperature=1.0
        )

        assistant_reply = response.choices[0].message.content
        try:
            liste_kat = temizle_ve_donustur(assistant_reply)
        except Exception as e:
            self.output_text.insert(tk.END, f"Hata oluştu: {e}\n")
            return

        toplam_puan = 0
        self.output_text.insert(tk.END, f"Analiz edilen kategoriler: {liste_kat}\n\n")

        for i in liste_kat:
            try:
                with open(kategori_isimleri[i], "r", encoding="utf-8") as f:
                    grup = json.load(f)
            except FileNotFoundError:
                self.output_text.insert(tk.END, f"{i} kategorisi için dosya bulunamadı.\n")
                continue

            sayi1, sayi2 = random.sample(range(len(grup)), 2)
            alt_toplam = 0

            for idx in [sayi1, sayi2]:
                soru = grup[idx]["question"]
                cevap = grup[idx]["answer"]

                cevap_penceresi = tk.Toplevel(self.master)
                cevap_penceresi.title("Mülakat Sorusu")
                tk.Label(cevap_penceresi, text=f"Soru: {soru}", wraplength=400).pack(pady=5)
                cevap_entry = tk.Text(cevap_penceresi, height=4, width=50)
                cevap_entry.pack(pady=5)
                puan_label = tk.Label(cevap_penceresi, text="")
                puan_label.pack(pady=5)

                def puanla():
                    aday_cevap = cevap_entry.get("1.0", tk.END).strip()
                    if not aday_cevap:
                        messagebox.showwarning("Uyarı", "Cevap boş olamaz.")
                        return

                    system_prompt1 = {
                        "role": "system",
                        "content": """You are an interview evaluator AI. Compare the applicant’s answer with the model answer and give a score from 1 to 10. Only return the score as a number."""
                    }

                    chat_history1 = [system_prompt1, {"role": "user", "content": f"""
                    Question: "{soru}"
                    Real Answer: "{cevap}"
                    Candidate Answer: "{aday_cevap}"
                    """}]

                    response1 = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=chat_history1,
                        max_tokens=50,
                        temperature=1.0
                    )
                    puan = int(response1.choices[0].message.content.strip())
                    nonlocal alt_toplam
                    alt_toplam += puan
                    puan_label.config(text=f"Verilen puan: {puan}")
                    cevap_penceresi.after(2000, cevap_penceresi.destroy)  # 2 sn sonra pencereyi kapat

                tk.Button(cevap_penceresi, text="Puanla", command=puanla).pack(pady=10)
                self.master.wait_window(cevap_penceresi)

            toplam_puan += alt_toplam

        self.output_text.insert(tk.END, f"\nToplam Puan: {toplam_puan}")

root = tk.Tk()
app = InterviewApp(root)
root.mainloop()
