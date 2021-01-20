from flask import Flask, render_template, request, send_file, flash, make_response, redirect
from flask_paginate import Pagination, get_page_parameter
from flask_caching import Cache
from settings import *
from io import StringIO
from os import path
import csv
import mediator

app = Flask(__name__)

# Used by "flash" for flashing comments or errors as popup
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# tell Flask to use the config (defined in settings.py)
app.config.from_mapping(CACHE_CONFIG)
cache = Cache(app)


def run(**kwargs):
    """When called it starts the website"""
    app.run(**kwargs)


@app.route('/')
def homepage():
    """A webpage which explains briefly the project and allows you to download the datasets or to go through them"""

    return render_template('homepage.html')


@app.route('/about')
def about():
    """A webpage with the member of the group"""
    return render_template('about.html')


@app.route('/documentation', defaults={'file': 'homepage'})
@app.route('/documentation/<file>')
def documentation(file):
    """Return a webpage with the docs of the project.

    Every webpage of the docs has it's name added after "/documentation/"
    This means that you can add all the webpages that you want and you won't need to write a single line of code,
    just add the html files to "templates/documentation/" and the .json files with the documentation to the
    folder containing all the .json written in "settings.py".

    Any eventual exception is purposefully caught here and not in mediator.py to show the error
    as a popup with flash()"""

    try:
        docs = mediator.getDocumentation(DOCS_PATH, file)
    except OSError as err:
        flash({
            'type': 'error',
            'header': 'Something went wrong!',
            'message': 'There was an error in loading the documentation. You are redirected to the Project Overview',
            'details': err,
        })
        return render_template('documentation/homepage.html')

    return render_template('documentation/%s.html' % file, docs=docs)


@app.route('/functions')
def functions():
    """A webpage which lets you select the operation you want to do with the datasets"""

    return render_template('functions.html')


@app.route('/download', methods=['POST'])
def download():
    """Allows to download the table computed as tsv file.

    Steps:
    1) Get what_to_download to know the name by which the table is stored in the cache. It will also be
        the name of the file. If for some reason it can't find it, it flashes a popup and redirect to the previous page
    1.1) If name_file is either diseaseTable or geneTable then it downloads the whole dataset from it's
        actual location, NOT from the cache.
    2) Get the table from the cache. If the data is None, it's likely that the cache has exceeded the timout
        defined in the config.py. You need to reload the page to compute again the table
    3) Extract from "data_to_save" which is a dictionary the rows and the labels of the table
    4) A csv.writer is instantiated. It needs StringIO
    5) Write as the first row the labels of the columns, then write all the rows
    6) Make a response which allows the .tsv file to be downloaded
    7) Set some information of the file that will be downloaded like its name and filetype

    """

    # Step 1)
    name_file = request.form.get('name_file')
    if name_file is None:
        flash({'type': 'warning',
               'header': 'Error!',
               'message': 'Error in downloading the table, please try reloading the page!'
                          '\n\nDetails: "name_file" not found in the forms'})
        return redirect(request.referrer)

    elif name_file == 'diseaseTable':
        # Compute the path to the databases
        disease_evidences_path = path.join(DATASET_LOCATION, DISEASE_TABLE_NAME)
        return send_file(disease_evidences_path, as_attachment=True)

    elif name_file == 'geneTable':
        # Compute the path to the databases
        gene_evidences_path = path.join(DATASET_LOCATION, GENE_TABLE_NAME)
        return send_file(gene_evidences_path, as_attachment=True)

    # Step 2)
    data_to_save = cache.get(TABLE_CACHE_NAME)
    if data_to_save is None:
        flash({'type': 'warning',
               'header': 'Something went wrong!',
               'message': 'I could not get the table to let you download it, please try reloading the page!'
                          '\n\nDetaild: The data is not in the cache!'})
        return redirect(request.referrer)

    # Step 3)
    rows = data_to_save['rows']
    labels = [data_to_save['labels']]

    # Step 4)
    si = StringIO()
    cw = csv.writer(si, delimiter='\t')

    # Step 5)
    cw.writerows(labels)
    cw.writerows(rows)

    # Step 6)
    output = make_response(si.getvalue())

    # Step 7)
    output.headers["Content-Disposition"] = f"attachment; filename={name_file}.tsv"
    output.headers["Content-type"] = "text/tsv"
    return output


@app.route('/browseGeneDataset')
def browseGeneDataset():
    """A webpage which lets you go through gene data table.
    To do the pagination it uses Pagination() from flask-paginate"""

    # variables
    data = mediator.getInfoGenes()
    rows_per_page = 30

    # Get the page from the form to let the user go to a specific page
    # The value of "page" is taken with functions from flask-paginate otherwise it raises errors
    page = int(request.args.get(get_page_parameter(), type=int, default=1))
    if page < 1:
        flash({'type': 'warning',
               'header': 'Warning!',
               'message': 'You need to insert a positive number!'})

    # start and end indexes of the table
    start = page * rows_per_page
    end = (page + 1) * rows_per_page

    # Returns a list of the rows from index start to index end
    data['rows'] = mediator.getDiseaseTableList(start, end)

    # Prepares the pagination that allows you to click the number of the page and view it in the webpage
    pagination = Pagination(page=page, total=data['nrows'], record_name="diseases entries",
                            css_framework='bulma', per_page=rows_per_page)

    return render_template('browseDiseasesDataset.html',
                           base_pmid_url=BASE_PMID_URL,
                           data=data,
                           pagination=pagination)


@app.route('/browseDiseasesDataset')
def browseDiseasesDataset():
    """A webpage which lets you go through gene data table.
    To do the pagination it uses Pagination() from flask-paginate"""

    # variables
    data = dict()
    data['nrows'] = mediator.getInfoDiseases()['nrows']
    data['labels'] = mediator.getInfoDiseases()['labels']
    per_page = 30

    # Get the page from the form to let the user go to a specific page
    # The value of "page" is taken with functions from flask-paginate otherwise it raises errors

    page = int(request.args.get(get_page_parameter(), type=int, default=1))
    if page < 1:
        flash({'type': 'warning',
               'header': 'Warning!',
               'message': 'You need to insert a positive number!'})

    # start and end index of the table
    start = page * per_page
    end = (page + 1) * per_page

    # Returns a list of the rows from index start to index end
    data['rows'] = mediator.getDiseaseTableList(start, end)

    # Prepares the pagination that allows you to click the number of the page and view it
    pagination = Pagination(page=page, total=data['nrows'], record_name="diseases entries",
                            css_framework='bulma', per_page=per_page)

    return render_template('browseDiseasesDataset.html',
                           base_pmid_url=BASE_PMID_URL,
                           data=data,
                           pagination=pagination)


# for a and b objective
@app.route('/info')
def info():
    """Returns a webpage with all the information about the data tables and a preview of heads and tails"""

    gene_data, disease_data = mediator.getInfo()

    return render_template('operations/info.html', gene_data=gene_data, disease_data=disease_data)


# for c objective
@app.route('/distinctGenes')
def distinctGenes():
    """A webpage with all the unique distinct genes in the gene table"""

    NAME_FUNCTION = 'distinct_genes'

    data = mediator.getDistinctGenes()

    cache.set(TABLE_CACHE_NAME, data)

    return render_template('operations/distinctGenes.html', data=data, NAME_FUNCTION=NAME_FUNCTION)


# for e objective
@app.route('/distinctDiseases')
def distinctDiseases():
    """A webpage with all the unique distinct disease in the disease table"""

    NAME_FUNCTION = 'distinct_diseases'

    data = mediator.getDistinctDiseases()

    cache.set(TABLE_CACHE_NAME, data)

    return render_template('operations/distinctDiseases.html', data=data, NAME_FUNCTION=NAME_FUNCTION)


# for d objective
@app.route('/geneEvidences', methods=["POST", "GET"])
def geneEvidences():
    """The first time the user access "geneEvidences" it is requested with 'GET' method.
    Then it returns a webpage which lets the user input a geneSymbol or a geneID.
    It is then submitted back to "geneEvidences" but with 'POST' method.
    Now it returns a webpage which lists all the evidences in literature of the gene"""

    NAME_FUNCTION = '_evidences'

    if request.method == "GET":
        return render_template('operations/inputGeneEvidences.html')
    else:
        gene = request.form['gene']
        data = mediator.getGeneEvidences(gene)

        cache.set(TABLE_CACHE_NAME, data)

        return render_template("operations/geneEvidences.html", gene=gene, data=data, NAME_FUNCTION=NAME_FUNCTION,
                               base_pmid_url=BASE_PMID_URL)


# for f objective
@app.route('/diseaseEvidences', methods=["POST", "GET"])
def diseaseEvidences():
    """The first time the user access "diseaseEvidences" it is requested with 'GET' method.
    Then it returns a webpage which lets the user input a diseaseID or a diseaseName.
    It is then submitted back to "diseaseEvidences" but with 'POST' method.
    Now it returns a webpage which lists all the evidences in literature of the disease"""

    NAME_FUNCTION = '_evidences'

    if request.method == "GET":
        return render_template('operations/inputDiseaseEvidences.html')
    else:
        disease = request.form['disease']
        data = mediator.getDiseaseEvidences(disease)

        cache.set(TABLE_CACHE_NAME, data)

        return render_template('operations/diseaseEvidences.html', disease=disease, data=data,
                               base_pmid_url=BASE_PMID_URL, NAME_FUNCTION=NAME_FUNCTION)


# for g objective
@app.route('/correlation', methods=["POST", "GET"])
def correlation():
    """The webpage lists the correlations between genes and diseases.

    It allows th user to customize the results, he can decide the number of correlations to show ("rows")
    and the minimum number of occurrences a correlation need to have to be shown ("occurrences").

    Occurrences ha priority over rows. In fact, if "occurrence" is given and the user hasn't written
    anything in "rows" then it sets "rows" to 0 which means that all rows will be returned.
    Also, if the user wants 50 rows, but the rows which meet the occurrence requirement are 30,
    only 30 rows will be returned.
    """

    # This is for the first time the user visits the page
    if request.method == "GET":
        nrows = 10
        occurrences = 0

    else:
        try:
            occurrences = request.form['occurrence']
            occurrences = int(occurrences)

            if occurrences < 0:
                occurrences = 0

        except ValueError:
            # If it raise ValueError it means "occurrence" it's a string which cannot be converted to a number.
            # It's either an empty string or a word. If it's an empty string it sets "occurrences" to the default value
            if occurrences != '':
                flash({'type': 'warning',
                       'header': 'Warning!',
                       'message': 'You need to insert a positive number!'})
                return redirect(request.referrer)
            else:
                occurrences = 0

        try:
            nrows = request.form['rows']
            nrows = int(nrows)

            if nrows < 0:
                flash({'type': 'warning',
                       'header': 'Warning!',
                       'message': 'You need to insert a positive number!'})
                return redirect(request.referrer)

        except ValueError:
            # If it raise ValueError it means it's a string which cannot be converted to a number.
            # It's either an empty string or a word. If it's an empty string it set "nrows" to the default value
            if nrows != '':
                flash({'type': 'warning',
                       'header': 'Warning!',
                       'message': 'You need to insert a number!'})
                return redirect(request.referrer)
            else:
                if occurrences != 0:
                    nrows = 0
                else:
                    nrows = 10

    data = mediator.getCorrelation(nrows, occurrences)

    NAME_FUNCTION = 'correlation'

    cache.set(TABLE_CACHE_NAME, data)

    return render_template('operations/correlation.html', data=data, NAME_FUNCTION=NAME_FUNCTION)


# for h objective
@app.route('/diseasesRelatedToGene', methods=["POST", "GET"])
def diseasesRelatedToGene():
    """The first time the user access "diseasesRelatedToGene" it is requested with 'GET' method.
    Then it returns a webpage which lets the user input a geneSymbol or a geneID.
    It is then submitted back to "diseasesRelatedToGene" but with 'POST' method.
    Now it returns a webpage which lists all the diseases related to the gene found in literature"""

    NAME_FUNCTION = 'diseases_rel_to_'

    if request.method == "GET":
        return render_template('operations/inputDiseasesRelatedToGene.html')
    else:
        gene = request.form['gene']
        data = mediator.getDiseasesRelatedToGene(gene)

        cache.set(TABLE_CACHE_NAME, data)

        return render_template("operations/diseasesRelatedToGene.html", gene=gene, data=data,
                               NAME_FUNCTION=NAME_FUNCTION)


# for i objective
@app.route('/genesRelatedToDisease', methods=["POST", "GET"])
def genesRelatedToDisease():
    """The first time the user access "genesRelatedToDisease" it is requested with 'GET' method.
    Then it returns a webpage which lets the user input a diseaseName or a diseaseID.
    It is then submitted back to "genesRelatedToDisease" but with 'POST' method.
    Now it returns a webpage which lists all the genes related to the disease found in literature"""

    NAME_FUNCTION = 'genes_rel_to_'

    if request.method == "GET":
        return render_template('operations/inputGenesRelatedToDisease.html')
    else:
        disease = request.form['disease']
        data = mediator.getGenesRelatedToDisease(disease)

        cache.set(TABLE_CACHE_NAME, data)
        return render_template("operations/genesRelatedToDisease.html", data=data, disease=disease,
                               NAME_FUNCTION=NAME_FUNCTION)


if __name__ == '__main__':
    import mediator

    app.run(debug=True)
