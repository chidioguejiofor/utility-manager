def capitalize_each_word_in_sentence(string):
    final_string = map(lambda x: x.capitalize(), string.split(' '))
    return ' '.join(final_string)
