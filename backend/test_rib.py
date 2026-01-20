from schwifty import IBAN

def check_iban(s):
    try:
        IBAN(s)
        return True
    except:
        return False

# The raw sequence from OCR might be FR76300020734400000040895C79 (27 chars)
raw = "FR76300020734400000040895C79"

# Let's try replacing C with 0
cand1 = raw.replace('C', '0')
print(f"Trying {cand1}: {check_iban(cand1)}")

# In the raw text, bank code 3000 is followed by 2... maybe it's 30002
# FR76 3000 2 07344 00000 04089 5 C 79?
# Wait, look at the digits: 3000 2 07344 00004 0895 C79
digits = "3000207344000040895C79" # 22 chars?
# Reconstructed needs 23 digits.
# Maybe a 0 is missing?
for i in range(len(digits)+1):
    for digit in "0123456789":
        test_digits = digits[:i] + digit + digits[i:]
        if len(test_digits) == 23:
            test_iban = "FR76" + test_digits.replace('C', '0')
            if check_iban(test_iban):
                print(f"MATCH FOUND: {test_iban}")

# Also try the raw 27-char if a digit was interpreted as a letter
# FR76 3000 2 07344 0000 4 089 5 C 7 9 -> too many?
