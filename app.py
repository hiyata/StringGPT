from flask import Flask, render_template, request
import requests
import openai

app = Flask(__name__)

openai.api_key = "ADD YOUR API KEY HERE"

def generate_gpt_response(input_text):
    # Call the OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input_text,
        max_tokens=250
    )
    return response.choices[0].text.strip()

def get_protein_info(protein_identifiers):
    protein_info = []

    for identifier in protein_identifiers:
        uniprot_api_url = f"https://www.ebi.ac.uk/proteins/api/proteins/{identifier}"
        response = requests.get(uniprot_api_url)

        if response.status_code == 200:
            protein_data = response.json()
            protein_info.append(protein_data)

    return protein_info


def get_string_results(protein_name):
    string_api_url = "https://version-11-5.string-db.org/api"
    output_format = "tsv-no-header"
    method = "interaction_partners"

    ## Construct the request
    request_url = "/".join([string_api_url, output_format, method])

    ## Set parameters
    params = {
        "identifiers": protein_name,  # Use the protein name provided
        "species": 9606,  # species NCBI identifier 
        "limit": 5,
        "caller_identity": "www.awesome_app.org"  
    }

    ## Call STRING
    response = requests.post(request_url, data=params)

    ## Read and parse the results
    results = []
    for line in response.text.strip().split("\n"):
        l = line.strip().split("\t")
        query_ensp = l[0]
        query_name = l[2]
        partner_ensp = l[1]
        partner_name = l[3]
        combined_score = l[5]

        result_entry = f"{query_ensp} ({query_name}) - {partner_ensp} ({partner_name}), Score: {combined_score}"
        results.append(result_entry)

    return results

@app.route("/", methods=["GET", "POST"])
def index():
    combined_results = []

    if request.method == "POST":
        protein_name = request.form.get("protein_name")

        # Get STRING results for the protein name
        string_results = get_string_results(protein_name)

        if string_results:
            combined_results.append("STRING Results:")
            combined_results.extend(string_results)

            # Add UniProt protein information to the combined_results list
            uniprot_info = get_uniprot_info(protein_name)
            if uniprot_info:
                combined_results.append("UniProt Protein Information:")
                combined_results.extend(uniprot_info)

            string_results_text = "\n".join(string_results)
            gpt_input = f"Given the STRING results:\n{string_results_text}\n\nQuery: Please provide insights about the STRING results. Include the confidence intervals and details about the interactions.\nAI:"
        
            # Generate a response using ChatGPT
            chatgpt_response = generate_gpt_response(gpt_input)

            combined_results.append("ChatGPT Response:")
            combined_results.append(chatgpt_response)

    return render_template("index.html", combined_results=combined_results)


    return render_template("index.html", combined_results=combined_results)



if __name__ == "__main__":
    app.run(debug=True)


