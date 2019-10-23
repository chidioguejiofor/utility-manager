serialization_error = {
    'required':
    "Missing data for required field.",
    'pass_is_required':
    'Password field is required',
    'alpha_numeric':
    'Only letters and numbers are allowed here',
    'alpha_only':
    "Only Alphabets are allowed here",
    'invalid_email':
    'Not a valid email address.',
    'already_exists':
    'The {} already exists',
    'invalid_field_data':
    "There are some fields data you provided that are invalid",
    'min_length_error':
    'This field must be greater than {} characters',
    'max_length_error':
    'This field must be less than {} characters',
    'login_failed':
    'Username or password was not found',
    'email_not_found':
    'The email you specified was not found',
    'already_verified':
    'User has already been verified',
    'invalid_url':
    '`redirectURL` field must be a valid URL',
    'invalid_image':
    'File is not a valid image',
    'invalid_confirmation_link':
    "You can't fake a confirmation link. C'mon! Be sure that link is from your email!",
    'not_an_admin':
    'You must a Manager or Owner in at least one organisation to do this',
    # 'at_les': ''
}

authentication_errors = {
    'token_expired':
    'Token you specified has expired',
    'unverified_user':
    'Only verified users can access this',
    'session_expired':
    'Your session has expired',
    'token_invalid':
    'Token you specified is invalid',
    'missing_token':
    'Auth requirements are missing. Please login again',
    'confirmation_expired':
    'Confirmation timed out. You would have to resend the email',
    'invalid_auth_header':
    'Authorization token must be in format `Bearer token_value`'
}

model_operations = {
    'both_greek_and_letter_are_none':
    ('There must be a value for either `greek_symbol_num` or `letter_symbol`',
     'There must be a value for either `greekSymbol` or `letterSymbol`'),
    'both_greek_and_letter_are_provided': (
        'Only one of `letter_symbol` or `greek_symbol_num` should have a value not both',
        'Only one of `letterSymbol` or `greekSymbol` should have a value not both',
    )
}
