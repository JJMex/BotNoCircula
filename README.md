# 🚗 Bot Hoy No Circula & Contingencia CDMX

![Python](https://img.shields.io/badge/Python-3.9-blue?style=flat&logo=python)
![Status](https://img.shields.io/badge/Status-Active-success)
![CDMX](https://img.shields.io/badge/Region-CDMX%2FMorelos-green)

Este bot vigila automáticamente las restricciones vehiculares de la Ciudad de México y el Estado de México. Te avisa diariamente qué autos descansan y **detecta en tiempo real si se activa una Contingencia Ambiental**.

---

## 🧠 Inteligencia del Bot

El sistema opera con un **Semáforo de 3 Estados** para mantenerte informado sin falsas alarmas:

| Estado | Significado | Acción del Bot |
| :--- | :--- | :--- |
| 🟢 **NORMAL** | Aire limpio / Sin avisos. | Muestra las reglas habituales del Hoy No Circula. |
| 🟡 **PREVENTIVA** | Rumores de contingencia. | Detecta palabras como *"posible"* o *"riesgo"*. Te avisa para que estés atento, pero mantiene las reglas normales. |
| 🚨 **ACTIVADA** | **FASE 1 CONFIRMADA.** | Detecta comunicado oficial. **Cambia las reglas a Doble Hoy No Circula** y te dice qué hologramas descansan. |

---

## ⚡ Funcionalidades Clave

* **📅 Lógica de Sábados:** Calcula matemáticamente si es el 1º, 2º, 3º, 4º o 5º sábado del mes para indicarte si descansan placas PARES o IMPARES.
* **☀️🌙 Doble Turno:**
    * **6:05 AM:** Reporte de **HOY** (para saber qué auto dejar).
    * **8:05 PM:** Reporte de **MAÑANA** (para planificar tu día).
* **🔗 Verificación:** Incluye enlaces directos a los tweets de la CAMe o noticias de Google News.

---

## 🚀 Configuración Rápida

Este bot corre en **GitHub Actions** (Gratis).

1.  Haz Fork de este repositorio.
2.  Ve a `Settings` > `Secrets and variables` > `Actions`.
3.  Agrega tus secretos de Telegram:
    * `TELEGRAM_TOKEN`
    * `TELEGRAM_CHAT_ID`
4.  Ve a la pestaña `Actions` y habilita el workflow.

¡Listo! El bot trabajará solo.

---

## 📸 Ejemplo de Alerta (Contingencia)

> 📡 _Tras analizar monitores atmosféricos y boletines oficiales, el reporte es el siguiente:_
>
> 🚨 **ESTADO: CONTINGENCIA FASE 1 (MAÑANA)**
> ──────────────────
> 📅 **JUEVES 15/05**
>
> ⛔ **RESTRICCIONES AMBIENTALES:**
> 🚫 **Holograma 2:** TODOS descansan.
> 🚫 **Holograma 1:** Terminación PAR/IMPAR + Placa habitual.
> 🚫 **Holograma 0/00:** Exentos.
>
> **🔍 CONFIRMACIÓN OFICIAL (Twitter CAMe):**
> SE ACTIVA FASE 1 DE CONTINGENCIA AMBIENTAL...
> 🔗 [Ver Tweet](https://twitter.com)

---

<p align="center">
  <i>Hecho para sobrevivir al tráfico chilango. 🇲🇽</i>
</p># BotNoCircula
