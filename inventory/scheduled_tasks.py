from datetime import datetime
from inventory import dicts_and_misc

char_val_map = dicts_and_misc.char_value_dict()
month_val_map = dicts_and_misc.month_val_dict()


def manipulate_booleans(doc_ref, update_data):
    doc_ref.update(update_data)


def scheduled_task_meal_analytics(which_meal, db):
    choice_collection_ref = db.collection("choice")
    choice_docs = choice_collection_ref.stream()

    choice_count = 0
    for doc in choice_docs:
        data = doc.to_dict()

        if data[f"{which_meal}"]:
            choice_count += 1
    print(choice_count)
    db.collection("count").document("3XAuDDcCBxPjeLnoJDZ5").set({f"{which_meal}": choice_count}, merge=True)

    if which_meal == "dinner":
        which_meal = "Dinner"
    elif which_meal == "snacks":
        which_meal = "Snacks"

    attendance_collection_ref = db.collection("attendance")
    attendance_docs = attendance_collection_ref.stream()

    attendance_count = 0
    for doc in attendance_docs:
        data = doc.to_dict()

        if data[f"{which_meal}"]:
            attendance_count += 1
    print(attendance_count)




def scheduled_task_daily(db):
    attendance_collection_ref = db.collection("attendance")
    attendance_docs = attendance_collection_ref.stream()

    for doc in attendance_docs:
        # data = doc.to_dict()

        new_data = {
            "breakfast": False,
            "lunch": False,
            "Snacks": False,
            "Dinner": False,
        }
        manipulate_booleans(doc.reference, new_data)

    choice_collection_ref = db.collection("choice")
    choice_docs = choice_collection_ref.stream()

    for doc in choice_docs:
        # data = doc.to_dict()

        new_data = {
            "breakfast": True,
            "lunch": True,
            "snacks": True,
            "dinner": True,
        }
        manipulate_booleans(doc.reference, new_data)


def scheduled_task_monthly(db):
    fee_dailies_ref = db.collection("fees").document("daily")
    fee_monthly_ref = db.collection("fees").document("monthly")

    fee_dailies_collection, fee_monthly_collection = fee_dailies_ref.get(), fee_monthly_ref.get()
    fee_dailies_collection, fee_monthly_collection = fee_dailies_collection.to_dict(), fee_monthly_collection.to_dict()

    current_month = datetime.now().strftime("%m")
    to_monthly = {}
    # to_daily = {}
    for keys in fee_dailies_collection:
        value = fee_dailies_collection[keys]
        valued = 0
        for value in value[:]:
            if value in char_val_map:
                valued += char_val_map[value]

        to_monthly[keys] = valued

    if current_month in month_val_map:
        current_month = month_val_map[current_month]
    for keys in fee_monthly_collection:
        value = fee_monthly_collection[keys]
        value[current_month] = to_monthly[keys]

    fee_monthly_ref.set(fee_monthly_collection, merge=True)

    for keys in fee_dailies_collection:
        fee_dailies_collection[keys] = "0000000000000000000000000000000"
    fee_dailies_ref.set(fee_dailies_collection, merge=True)
    # print(fee_monthly_collection)
