import pandas as pd

##### TOUR PLOT FUNCTIONS #####
# NOTE THAT THE X MATRIX IS NOT SYMMETRICAL. 
# ORIGINS INCLUDE THE START DEPOT AS THE FIRST INDEX, DESTINATIONS INCLUDE THE LAST DEPOT AS THE LAST INDEX.
# ROW INDEX IS 1 ABOVE THE COLUMN INDEX IF WE WANT TO REFERENCE THE SAME POINT
def out(X_df: pd.DataFrame) -> dict:
    '''Takes in the X dataframe to get all the x_ij = 1. Returns the outflowing neighbour of each node.'''
    n = len(X_df)
    my_dict = {}
    for i in range(n):
        for j in range(n):
            if round(X_df.iloc[i,j]) == 1:
                my_dict[i] = (i, j+1) 
    return my_dict


def get_tours(X_df: pd.DataFrame) -> list:
    '''Takes in the X dataframe and returns the tour sequence. Index 0 is the start location, index n+1 is the end location.'''
    dic = out(X_df)
    n = len(X_df)
    
    # Initilisation
    lst = []
    lst.append(0)
    cur = dic[0][1]
    
    while cur != n:
        lst.append(cur)
        cur = dic[cur][1]
    return lst