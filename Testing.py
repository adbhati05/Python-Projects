name = input("Who is the patient being entered into the system? ")
age =  input("How old is the patient? ")
status = input("What is the current condition of the patient? (EM = emaciated, EX = exhausted, IP = in pain, MU = mentally unstable) ")
procedure = "Sign patient out of hospital."

if status == "EM":
    procedure = "Inform nurse and have them put the patient on a new diet and nutritional plan."
    status = "Emaciated"
elif status == "EX":
    procedure = "Have nurse place patient in bed and prepare them to rest."
    status = "Exhausted"
elif status == "IP":
    procedure = "Have nurse place patient on painkillers and prepare them to rest."
    status = "Currently in pain"
elif status == "MU":
    procedure = "Inform local psychiatric hospital and immediately have patient registered into their system for assistance."

print("Patient name: " + name)
print("Patient age: " + str(age))
print("Patient status: " + status)
print(procedure)