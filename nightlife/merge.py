import pandas as pd

# Load both CSV files
nightlife_df = pd.read_csv('nightlife.csv')
output_df = pd.read_csv('output.csv',encoding='ISO-8859-1')

# Merge data based on 'listingtitle' and 'listingaddress'
merged_df = nightlife_df.merge(
    output_df[["Listing Title",	"Listing Email",	"Listing URL",	"Listing Address",	"Listing Short Description",	"Listing Long Description"]],
    on=['Listing Title', 'Listing Address'],
    how='left',
    suffixes=('', '_new')  # Append _new to the columns from output_df to avoid overwriting directly
)

# Update only the existing columns where a new value is available (not null)
for column in ['Listing Email', 'Listing URL', 'Listing Short Description', 'Listing Long Description']:
    merged_df[column] = merged_df[f'{column}_new'].combine_first(merged_df[column])
    merged_df.drop(columns=[f'{column}_new'], inplace=True)
merged_df.to_csv('nightlife_updated.csv', index=False)

print("Merged data saved to nightlife_updated.csv")
