from flask import Flask, render_template, request, redirect, url_for, send_file
import xml.etree.ElementTree as ET
import requests
import os
from datetime import datetime

app = Flask(__name__)
DATA_DIR = "data"
XML_FILE = os.path.join(DATA_DIR, "kaynaklar.xml")

# XML Dosyasını Oluşturma
def create_xml_file():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    root = ET.Element("WebKaynaklari")
    tree = ET.ElementTree(root)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)

# XML'e Veri Ekleme
def add_to_xml(data):
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()

        # Kaynak verilerini XML'e ekle
        kaynak = ET.SubElement(root, "Kaynak")
        for key, value in data.items():
            elem = ET.SubElement(kaynak, key)
            elem.text = value

        tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)
        print("Veri XML dosyasına eklendi.")
    except Exception as e:
        print(f"XML dosyasına ekleme hatası: {e}")

# URL Erişilebilirlik Kontrolü
def check_accessibility(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Raporu TXT dosyasına kaydet
def save_report_to_txt(report_data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = os.path.join(DATA_DIR, f"rapor_{timestamp}.txt")
    
    with open(report_filename, "w") as file:
        for entry in report_data:
            file.write(f"KaynakID: {entry['KaynakID']}\n")
            file.write(f"KaynakAdi: {entry['KaynakAdi']}\n")
            file.write(f"KaynakURL: {entry['KaynakURL']}\n")
            file.write(f"Durum: {entry['Durum']}\n\n")
    print(f"Rapor {report_filename} olarak kaydedildi.")
    return report_filename  # Return the report filename for download

# Anasayfa (Form)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Formdan gelen verileri al
        kaynak_id = request.form.get("kaynakID")
        kaynak_adi = request.form.get("kaynakAdi")
        kaynak_detay = request.form.get("kaynakDetay")
        kaynak_url = request.form.get("kaynakURL")
        kaynak_zaman_damgasi = datetime.now().isoformat()

        # XML'e kaydet
        data = {
            "KaynakID": kaynak_id,
            "KaynakAdi": kaynak_adi,
            "KaynakDetay": kaynak_detay,
            "KaynakURL": kaynak_url,
            "KaynakZamanDamgasi": kaynak_zaman_damgasi,
        }
        add_to_xml(data)
        return redirect(url_for("report"))

    return render_template("form.html")

# Rapor Sayfası
@app.route("/report")
def report():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    report_data = []
    for kaynak in root.findall("Kaynak"):
        url = kaynak.find("KaynakURL").text
        status = "Erişilebilir" if check_accessibility(url) else "Erişilemez"
        report_data.append({
            "KaynakID": kaynak.find("KaynakID").text,
            "KaynakAdi": kaynak.find("KaynakAdi").text,
            "KaynakURL": url,
            "Durum": status,
        })

    # Raporu TXT dosyasına kaydet
    report_filename = save_report_to_txt(report_data)

    return render_template("report.html", report_data=report_data, report_filename=report_filename)

# Raporu İndirme
@app.route("/download_report/<filename>")
def download_report(filename):
    report_path = os.path.join(DATA_DIR, filename)
    return send_file(report_path, as_attachment=True)

if __name__ == "__main__":
    # XML dosyasının başlangıçta oluşturulması
    create_xml_file()
    app.run(debug=True)
