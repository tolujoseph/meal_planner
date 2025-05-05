import openai
import pandas as pd
from fpdf import FPDF
from telegram import Bot

# ------------------- CONFIG -------------------
openai.api_key = "openai_api_key"
TELEGRAM_TOKEN = "telegram_token" 
TELEGRAM_CHAT_ID = "telegram_user_id" 

MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

USER_PREFS = {
    "diet": "vegetarian",
    "avoid": ["mushrooms", "tofu"],
    "cooking_time": "under 30 minutes"
}
# ------------------------------------------------


def generate_meal(meal_type):
    prompt = (
        f"Suggest a {meal_type.lower()} meal for a {USER_PREFS['diet']} diet, "
        f"avoiding {', '.join(USER_PREFS['avoid'])}, that takes {USER_PREFS['cooking_time']} to prepare. "
        f"Respond with: Meal name and Ingredients list."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']


def build_meal_plan():
    plan = []
    grocery_set = set()

    for day in DAYS:
        for meal in MEAL_TYPES:
            print(f"[INFO] Generating {meal} for {day}")
            result = generate_meal(meal)
            lines = result.split("\n")
            meal_name = lines[0].strip()
            ingredients = [line.strip("- ").strip() for line in lines[1:] if line.strip()]
            plan.append([day, meal, meal_name])
            grocery_set.update(ingredients)

    df = pd.DataFrame(plan, columns=["Day", "Meal", "Dish"])
    return df, sorted(grocery_set)


def export_to_pdf(meal_df, grocery_list, filename="meal_plan.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Weekly Meal Plan", ln=True, align="C")
    pdf.ln(5)

    current_day = ""
    for _, row in meal_df.iterrows():
        if row["Day"] != current_day:
            current_day = row["Day"]
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"\n{current_day}", ln=True)
            pdf.set_font("Arial", size=12)

        pdf.cell(0, 10, f"{row['Meal']}: {row['Dish']}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Grocery List", ln=True)
    pdf.set_font("Arial", size=12)
    for item in grocery_list:
        pdf.cell(0, 10, f"- {item}", ln=True)

    pdf.output(filename)
    print(f"[INFO] Meal plan saved to {filename}")


def send_pdf_to_telegram(file_path):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        with open(file_path, 'rb') as file:
            bot.send_document(
                chat_id=TELEGRAM_CHAT_ID,
                document=file,
                filename="meal_plan.pdf",
                caption="📅 Here's your weekly meal plan and grocery list!"
            )
        print("[INFO] Sent PDF to Telegram")
    except Exception as e:
        print(f"[ERROR] Failed to send PDF to Telegram: {e}")


def main():
    meal_df, groceries = build_meal_plan()
    export_to_pdf(meal_df, groceries)
    send_pdf_to_telegram("meal_plan.pdf")


if __name__ == "__main__":
    main()
