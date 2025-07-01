def caesar_cipher(text, shift):
    result = ""

    for char in text:
        if char.isalpha():
            # Shift uppercase characters
            if char.isupper():
                result += chr((ord(char) + shift - 65) % 26 + 65)
            # Shift lowercase characters
            else:
                result += chr((ord(char) + shift - 97) % 26 + 97)
        else:
            # Non-alphabet characters are added as-is
            result += char

    return result

# Example usage
plain_text = "hello"
shift_value = 4
encrypted_text = caesar_cipher(plain_text, shift_value)
print("Encrypted:", encrypted_text)

# To decrypt, just use negative shift
decrypted_text = caesar_cipher(encrypted_text, -shift_value)
print("Decrypted:", decrypted_text)
