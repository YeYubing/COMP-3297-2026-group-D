
ROLE_OWNER = 'owner'
ROLE_DEVELOPER = 'developer'


def get_allowed_transitions(current_status, role):
    allowed = []
    for (old, new), roles in TRANSITION_RULES.items():
        if old == current_status and role in roles:
            allowed.append(new)
    return list(dict.fromkeys(allowed))

TRANSITION_RULES = {
    ('new', 'open'): [ROLE_OWNER],
    ('new', 'rejected'): [ROLE_OWNER],
    ('new', 'duplicate'): [ROLE_OWNER],
    ('fixed', 'reopened'): [ROLE_OWNER],
    ('fixed', 'resolved'): [ROLE_OWNER], 
    ('open', 'assigned'): [ROLE_DEVELOPER],
    ('reopened', 'assigned'): [ROLE_DEVELOPER],
    ('assigned', 'fixed'): [ROLE_DEVELOPER],
    ('assigned', 'cannot_reproduce'): [ROLE_DEVELOPER],
}

def is_transition_allowed(old_status, new_status, user_role):
    if old_status == new_status:
        return True
    key = (old_status, new_status)
    allowed_roles = TRANSITION_RULES.get(key, [])
    return user_role in allowed_roles
