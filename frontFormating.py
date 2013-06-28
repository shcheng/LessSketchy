#
# frontFormating.py
#
# Collection of function to handle web formating and
# related needs of the front end.
#

def get_sketchyLevel(score):
    """Returns the sketchy labels"""
    label = []
    if score>=0.65:
        label = ['btn btn-danger btn-mini', 'Sketchy']
    elif score<=0.35:
        label = ['btn btn-success btn-mini', 'Seems Legit']
    else:
        label = ['btn btn-warning btn-mini', 'Hard to tell']
    return label[0], label[1]

def get_hint(feature_row):
    """
    Returns the hint that is to be printed  when hovering
    over the risk assessment button
    """
    hint_string = ''
    ## Hint row 1: Price/nbr ##
    nprice_diff = feature_row[-1]
    if nprice_diff>0:
        hint_string = '<font color="green">%d%%</font> greater than the median ' \
                      % int(nprice_diff*100)
    elif nprice_diff<0:
        hint_string = '<font color="red">%d%%</font> less than the median' \
                      % int(nprice_diff*100)
    else:
        hint_string = '<i class="icon-remove icon-white"></i> Price'
    ## Hint row 2: Address ##
    if feature_row[0]:
        hint_string += '<br><i class="icon-ok icon-white"></i> \
                        <font color="green">Address</font>'
    else:
        hint_string += '<br><i class="icon-remove icon-white"></i> \
                        <font color="red">Address</font>'
    ## Hint row 3: Phone number ##
    if feature_row[1]:
        hint_string += '<br><i class="icon-ok icon-white"></i> \
                        <font color="green">Phone</font>'
    else:
        hint_string += '<br><i class="icon-remove icon-white"></i> \
                        <font color="red">Phone</font>'
    ## Hint row 4: Frac of cap letters ##
    if int(feature_row[4]*100)>7:
        hint_string += '<br><font color="red">%d%% of capital letters</font>' \
                       % int(feature_row[4]*100)
    else:
        hint_string += '<br><font color="green">%d%% of capital letters</font>' \
                       % int(feature_row[4]*100)
    ## Hint row 5: Number of words ##
    hint_string += '<br>%d words' \
                   % int(feature_row[5])
    """
    if int(feature_row[5]*100)>80:
        hint_string += '<br><font color="red">%d words</font>' \
                       % int(feature_row[5])
    else:
        hint_string += '<br><font color="green">%d words</font>' \
                       % int(feature_row[5])
    """
    return hint_string


