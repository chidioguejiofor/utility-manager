serialization_error = {
    'required': "Missing data for required field.",
    'pass_is_required': 'Password field is required',
    'alpha_numeric': 'Only letters and numbers are allowed here',
    'alpha_only': "Only Alphabets are allowed here",
    'invalid_email': 'Not a valid email address.',
    'already_exists': 'The {} already exists',
    'invalid_field_data':
    "There are some fields data you provided that are invalid",
    'min_length_error':
    'This field must be greater than or equal to {} characters',
    'max_length_error': 'This field must be less than {} characters',
    'login_failed': 'Invalid login Credentials',
    'email_not_found': 'The email you specified was not found',
    'already_verified': 'User has already been verified',
    'invalid_url': '`redirectURL` field must be a valid URL',
    'invalid_image': 'File is not a valid image',
    'invalid_confirmation_link': "Link is expired",
    'not_an_admin':
    'You must a Manager or Owner in at least one organisation to do this',
    'not_found': '{} was not found',
    'already_added':
    'Some {}(s) you specified, have already been added this {}',
    'exists_in_org': "A {} with those values has already been created",
    'empty_update_data':
    "You did not specify any data you would like to update",
    'some_ids_not_found': "There are {} ids you specified that were not found"
}

authentication_errors = {
    'token_expired':
    'Your session has expired. Please login again',
    'unverified_user':
    'Only verified users can access this',
    'session_expired':
    'Your session has expired',
    'token_invalid':
    'Auth requirements are missing. Try logging in again.',
    'token_error':
    'Auth requirements are missing. Please login again',
    'missing_token':
    'Auth requirements are missing. Please login again',
    'confirmation_expired':
    'Confirmation timed out. You would have to resend the email',
    'invalid_auth_header':
    'Authorization token must be in format `Bearer token_value`',
    'forbidden':
    "You don't have permission to perform this operation",
    'invalid_reset_link':
    'The reset link is invalid or has expired. Please try again',
    'login_limit_reached':
    'You have made too many login attempts. Please try again in about {} minutes',
}

password_change_errors = {
    'new_pass_and_change_pass_are_eq':
    'Both currentPassword and newPassword should not be the same',
    'current_pass_is_invalid': 'Current password you specified is not correct'
}
parameter_errors = {
    'invalid_validations': f'A maximum of 4 validations is allowed',
    'invalid_validation_format': 'Invalid validation format `{}`',
    'multiple_validation_for_key':
    'You cannot provide multiple validation for `{}`',
    'value_not_a_number': 'The value `{}` for `{}` is not a number',
    'number_not_a_date':
    'Please provide a valid ISO {} for arg `{}` instead of a number',
    'invalid_date': 'The value {} is not a valid Date/DateTime',
    'missing_validation_for_type':
    'A validation must be provided when valueType is {}',
    'enum_has_one_field': 'An ENUM should have more than one field in it',
    'invalid_validation_key': '{} is not an unknown validation key'
}

model_operations = {
    'both_greek_and_letter_are_none':
    ('There must be a value for either `greek_symbol_num` or `letter_symbol`',
     'There must be a value for either `greekSymbol` or `letterSymbol`'),
    'both_greek_and_letter_are_provided': (
        'Only one of `letter_symbol` or `greek_symbol_num` should have a value not both',
        'Only one of `letterSymbol` or `greekSymbol` should have a value not both',
    ),
    'ids_not_found':
    'Some ids you specified were not found',
    'column_must_have_a_value':
    'The "{}" column cannot be empty'
}

invitation_errors = {
    'invites_already_sent_to_email':
    'This email has already been sent invitation',
    'duplicate_email_in_request':
    'This email was specified more that once in this request',
    'missing_role_ids': 'Some role IDs you specified do not exist',
    'cannot_add_role': "You don't have permission to invite a {}.",
    'email_already_in_org':
    "This user is already a member of your organisation"
}
