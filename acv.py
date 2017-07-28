#!/usr/bin/python
"""
    Note: This is written in python 2. Only a few small changes would be
    necessary for python 3 - notably changing `iterkeys` and `iteritems` to
    `keys` and `items` and `basestring` to `str`.

    For the purposes of simplicity, I'm going to assume that whereever the
    spec said "JSON object", we can just use a python dict. If not,
    generally what we get from a web service call is a string representing
    a JSON object, which can be turned into a Python dict using
        import json
        filter_object = json.loads(json_string)
"""

# Global object to store filters.
user_filters = {}


def checkFilter(filter, vehicle_object):
    """ Internal function to check if a filter matches a vehicle_object.
        Returns True if it does, False if it doesn't.
    """
    for key, values in filter.iteritems():
        # Make sure the key is in the vehicle object
        if key not in vehicle_object:
            return False
        vehicle_value = vehicle_object[key]
        # If values is a simple string, just compare it to the vehicle_value.
        if isinstance(values, basestring):
            # If they don't match, this isn't the vehicle for this filter.
            if vehicle_value != values:
                return False
        elif isinstance(values, list):
            # Check each value in the list
            if vehicle_value not in values:
                return False
        else:
            # This is an error. The error checking that should have preceeded
            # storeFilters failed somewhere along the way. Maybe I should
            # raise an exception, or maybe we just ignore it and the user
            # doesn't get a notification for this filter.
            return False

    return True


def checkUserFilters(userId, vehicle_object):
    """ Internal function to check if a user matches a vehicle_object.
        Returns True if it does, False if it doesn't.
    """
    filters = user_filters[userId]
    for f in filters:
        if checkFilter(f, vehicle_object):
            return True

    return False


def getUserIdsToNotify(vehicle_object):
    """ vehicle_object is a python dict containing some/all of:
                make
                model
                year
                trim
                transmission_type
                type
        all of which are strings, except year which is an int
        No error checking will be done on this dict - assume somebody already
        took care of validating that the provided information is logical and
        correct (ie they don't specify a year in two digits or use a "type"
        that isn't one of the known types or use a key that isn't in that
        list.)

        Returns a list of int of userids who need to be notified that this
        vehicle meets one of their filters. A userid needs to be notified if
        they store a filter_object (see storeFiltersForUser) that matches all
        the keys in the filter with corresponding keys in the vehicle_object.
        If they specify a list of values for a key, then the corresponding key
        in the vehicle_object only has to match one element in the list to be
        considered to match that key.

        Make sure to only return the same userid once! We don't want to ping
        people twice for the same vehicle.
    """
    ret_list = []
    for user in user_filters.iterkeys():
        if checkUserFilters(user, vehicle_object):
            ret_list.append(user)
            continue
    return ret_list


def storeFiltersForUser(userId, filter_object):
    """ userid is an int. Assume each userid can store any number of filters.
        filter_object is a python dict containing some/all of
                make
                model
                year
                trim
                transmission_type
                type
        all of which are strings or ints (year only) and a list of strings or
        ints.
        The filter is stored, and nothing is returned.
        No error checking will be done on the dict to make sure the values
        make sense or they use keys that aren't in the list. If they specify
        keys that aren't in the list, they probably won't get a match.
    """
    global user_filters
    # Does user already have a filter
    if userId not in user_filters:
        user_filters[userId] = []
    # Just add the filter to the list of filters for this user
    user_filters[userId].append(filter_object)
    return


if __name__ == '__main__':
    """ Test code goes here """

    """ Create some user filters """
    storeFiltersForUser(1, {
        'make': 'Toyota',
        'year': [2012, 2013, 2014],
        'model': 'Prius',
        })
    storeFiltersForUser(2, {
        'year': [2014, 2015, 2016],
        'type': 'pickup truck',
        })
    # This could overlap the first filter - make
    # sure the user is only pinged once!
    storeFiltersForUser(1, {
        'make': ['Toyota', 'Honda', 'Ford'],
        'transmission_type': ['manual', 'cvt'],
        'type': 'hybrid',
        })
    storeFiltersForUser(3, {
        'make': ['Toyota', 'Honda', 'Ford'],
        'transmission_type': ['manual', 'cvt'],
        'type': 'hybrid',
        })
    storeFiltersForUser(1, {
        'type': 'sports car',
        })
    # An invalid key. Should never match anything.
    storeFiltersForUser(4, {
        'xxxx': 'sports car',
        })
    assert len(user_filters) == 4
    print("Passed test: len(user_filters) = %d" % len(user_filters))

    notify = getUserIdsToNotify({
        'make': 'Toyota',
        'model': 'Prius',
        'year': 2014,
        'trim': 'LX',
        'transmission_type': 'cvt',
        'type': 'hybrid',
        })
    print notify
    assert len(notify) == 2
    print("passed test: %d users returned" % len(notify))
    assert 1 in notify
    print("passed test: userid 1 to be notified")
    assert 3 in notify
    print("passed test: userid 3 to be notified")

    notify = getUserIdsToNotify({
        'make': 'Chevrolet',
        'model': 'Camaro',
        'year': 2007,
        'trim': 'SS 1LE',
        'transmission_type': 'manual',
        'type': 'sports car',
        })
    assert len(notify) == 1
    print("passed test: %d users returned" % len(notify))
    assert 1 in notify
    print("passed test: userid 1 to be notified")

    notify = getUserIdsToNotify({
        'make': 'Ford',
        'model': 'F100',
        'year': 2014,
        'trim': 'XXX',
        'transmission_type': 'automatic',
        'type': 'pickup truck',
        })
    assert len(notify) == 1
    print("passed test: %d users returned" % len(notify))
    assert 2 in notify
    print("passed test: userid 2 to be notified")

    # Test a few that shouldn't match anything.
    notify = getUserIdsToNotify({
        'make': 'Ford',
        'model': 'Focus',
        'year': 2008,
        'trim': 'base',
        'transmission_type': 'automatic',
        'type': 'compact',
        })
    assert len(notify) == 0
    print("passed test: %d users returned" % len(notify))

    notify = getUserIdsToNotify({
        'make': 'Ford',
        'model': 'F100',
        'year': 2010,
        'trim': 'XXX',
        'transmission_type': 'automatic',
        'type': 'pickup truck',
        })
    assert len(notify) == 0
    print("passed test: %d users returned" % len(notify))
