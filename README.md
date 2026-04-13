# 🔋 Battery Current Restrictor (Victron Venus OS Add-on)

Ein Add-on für **Victron Venus OS**, das den Ladestrom deines Batteriesystems aktiv begrenzt.

## 🚀 Features

- 🔍 Überwachung des aktuellen Batterieladestroms
- ⚖️ Vergleich mit zulässigem Ladestrom durch BMS-Vorgabe
- ⚖️ Vergleich mit konfigurierbarer Ladekurve
- 🔧 Dynamische Anpassung des **Grid Set Points**, wenn Grenzwerte überschritten werden

### 🧠 Geplante Features

- ☀️ Intelligente Ladeplanung basierend auf PV-Ertragsprognosen

---

## ⚙️ Funktionsweise

Der Battery Current Restrictor arbeitet nach folgendem Prinzip:

1. Ermittlung des aktuellen Ladestroms
2. Berechnung des zulässigen Ladestroms basierend auf (kleinster Wert gewinnt):
   - Vorgabe des BMS
   - (zukünftig) konfigurierbare Ladekurve in Abhängigkeit von SOC
   - (zukünftig) PV-Forecast
3. Berechnung der Differenz Ist vs. Soll und Anpassung des **Grid Set Points**, falls der Ist-Wert den Soll-Wert überschreitet

---

## 📦 Installation

Führe die folgenden Befehle auf deinem Venus OS System aus:

```bash
wget https://github.com/schnitzel001/BatteryCurrentRestrictor/archive/refs/heads/master.zip
unzip master.zip
mkdir -p /data/battery-current-restrictor/service
cp -r BatteryCurrentRestrictor-master/* /data/battery-current-restrictor/
```
Führe ggf. notwendige Anpassungen in /data/battery-current-restrictor/config.json durch.

Schließe die Installation danach ab mit:

```bash
chmod +x /data/battery-current-restrictor/install.sh
/data/battery-current-restrictor/install.sh
# cleanup
rm -f master.zip
rm -rf BatteryCurrentRestrictor-master
```

## ⚙️ Konfiguration

Über die enthaltene config.json können einzelne Begrenzungen (de-)aktiviert sowie konfiguriert werden. Nachdem Änderungen an der Datei vorgenommen wurden ist ein Service-restart notwendig. Dazu Venus OS rebooten oder install.sh erneut ausführen.

## ⚡ Update

Führe die unter Installation genannten Schritte erneut aus.

## ⚠️ Sicherheitshinweis ⚠️

Dieses Add-in greift aktiv in die Steuerung des Energiesystems ein.
Falsche Konfiguration kann zu unerwartetem Verhalten führen.

  => Nutzung auf eigene Verantwortung!
