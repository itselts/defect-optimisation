# Points penalty for letting a task go overdue
def penalty(number_of_days, p):
    if number_of_days == 0:
        return p
    else:
        return 0