import json
from random import random, choice

import pandas as pd
from ipyleaflet import Map, basemaps, GeoJSON
from shiny import render_plot
from shiny.express import ui, render, input
from shinywidgets import render_plotly, render_widget
from helpers import read_data, annual_sum, annual_sum_by_prescription, prescription_by_lcg, annual_count, \
    annual_spend_by_year, annual_top_10, conditions_by_bnf_chapter
import plotly.express as px

path_prescriptions = './data/prescribing_data'
path_practice_details = './data/practice_name'

# Dataframes
prescriptions = read_data(path_prescriptions)
annual_sum_total = annual_sum(prescriptions)
annual_sum_count = annual_count(prescriptions)
annual_top_10_count = annual_top_10(prescriptions)
top_10_by_year_data = annual_top_10_count.sort_values('Count', ascending=False)
prescription_lcg = prescription_by_lcg(prescriptions)
conditions_bnf_chapter = conditions_by_bnf_chapter(prescriptions)

practice_details_df = pd.read_csv("./data/practice_name/2024october.csv", encoding='Windows-1252', engine='pyarrow',
                                  usecols=["LCG", "Registered_Patients"], dtype_backend='pyarrow')

prescribed_data = annual_sum_by_prescription(prescriptions)
ui.h1("Northern Ireland prescription Data")
ui.p("Data sources: ", ui.a({'href': f'https://www.opendatani.gov.uk/'}, 'OpenDataNI'))

with ui.navset_pill(id="tab"):
    with ui.nav_panel('Overall'):
        with ui.layout_columns():
            with ui.card():
                # Card Title
                "Annual Spend by Year"

                annual_spend_by_year_data = annual_spend_by_year(prescriptions)


                @render_plotly
                def annual_spend_total_by_year():
                    annual_spend_by_year_figure = px.bar(annual_spend_by_year_data, y='Gross Cost (£)', x='Year',
                                                         title='Annual Spend')
                    return annual_spend_by_year_figure

            with ui.card():
                @render_plotly
                def practice_details():
                    patients_by_lcg = practice_details_df.groupby('LCG')["Registered_Patients"].sum().reset_index()
                    lcg_distribution = px.pie(patients_by_lcg, values='Registered_Patients', names='LCG',
                                              title='Registered Patients by Area')
                    lcg_distribution.update_traces(textinfo="value+label", textposition='inside')
                    return lcg_distribution

        with ui.card():
            @render_widget
            def map():
                with open('./data/trustboundaries.geojson') as f:
                    data = json.load(f)

                def trust_style(feature):
                    trust_name = feature["properties"].get("TrustCode", "Unknown")
                    trust_colors = {
                        "BHSCT": "red",
                        "SHSCT": "green",
                        "NHSCT": "blue",
                        "WHSCT": "orange",
                        "SEHSCT": "purple"

                    }

                    fill_color = trust_colors.get(trust_name, "gray")  # Default color if TrustName is missing

                    return {
                        "color": "black",  # Border color
                        "weight": 2,  # Border thickness
                        "fillColor": fill_color,  # Fill color based on TrustName
                        "fillOpacity": 0.6,  # Transparency
                    }

                geo_json = GeoJSON(data=data, style={'opacity': 1, 'dashArray': '9', 'fillOpacity': 0.4, 'weight': 1},
                                   style_callback=trust_style)

                center = (54.78771490, -6.7)
                zoom = 8
                map_of_trusts = Map(basemap=basemaps.CartoDB.Positron, center=center, zoom=zoom)
                return map_of_trusts.add(geo_json)

    with ui.nav_panel('Reactive Top 10 Charts'):
        with ui.layout_sidebar():
            with ui.sidebar():
                'Filters'
                ui.input_select('daterange', 'Select year',
                                {'2025': 2025, '2024': 2024, '2023': 2023, '2022': 2022, '2021': 2021, '2020': 2020,
                                 '2019': 2019, '2018': 2018, '2017': 2017, '2016': 2016, '2015': 2015, '2014': 2014,
                                 '2013': 2013})
                ui.input_text('prescribed_item', 'Prescribed Item', 'Filter by', autocomplete='on',
                              placeholder='Filter by')
                ui.input_select('lcg_select', 'Select Region',
                                {'Northern': 'Northern', 'Southern': 'Southern', 'Western': 'Western',
                                 'Belfast': 'Belfast', 'South Eastern': 'South Eastern'})


            @render_plotly
            def top_10_by_year_count():
                top_10_by_year_data = annual_top_10_count.sort_values('Count', ascending=False)
                top_10_by_year_data = top_10_by_year_data[top_10_by_year_data['Year'] == int(input.daterange())]
                top_10_by_year_data = top_10_by_year_data.head(10)
                top_10_by_year_figure = px.bar(top_10_by_year_data, x='Count',
                                               y='VMP_NM',
                                               title=f'Top 10 Prescribed drugs in {input.daterange()} by Quantity',
                                               text_auto=True)
                return top_10_by_year_figure


            @render_plotly
            def top_10_by_year_cost():
                top_10_by_year_data = prescribed_data.sort_values('Gross Cost (£)', ascending=False)
                top_10_by_year_data = top_10_by_year_data[top_10_by_year_data['Year'] == int(input.daterange())]
                top_10_by_year_data = top_10_by_year_data.head(10)
                top_10_by_year_figure = px.bar(top_10_by_year_data, x='Gross Cost (£)',
                                               y='VMP_NM',
                                               title=f'Top 10 Prescribed drugs in {input.daterange()} by Cost',
                                               text_auto=True)
                return top_10_by_year_figure


            @render_plotly
            def prescriptions_lcg():
                top_10_by_lcg = prescription_lcg
                selected_region = input.lcg_select()
                top_10_by_lcg = top_10_by_lcg[(top_10_by_lcg['LCG'] == selected_region)]
                top_10_by_lcg = top_10_by_lcg[top_10_by_lcg['Year'] == int(input.daterange())]

                figure_top_10_lcg = px.pie(top_10_by_lcg.sort_values('Count', ascending=False).head(10), values='Count',
                                           names='VMP_NM',
                                           title=f'Top 10 Prescribed in : {"".join(selected_region)} Region in {input.daterange()}, by count')
                figure_top_10_lcg.update_traces(textinfo='value')
                return figure_top_10_lcg


            @render_plotly
            def conditions_bnf():
                conditions_data = conditions_bnf_chapter
                conditions_data = conditions_data[
                    (conditions_data['Year'] == int(input.daterange())) &
                    (conditions_data['LCG'] == input.lcg_select())
                    ]
                figure_conditions = px.bar(conditions_data, y='BNF_Chapter_Name', x='Count',
                                           title=f'Prescribed for by BNF Chapters in {"".join(input.lcg_select())} Region {input.daterange()}',
                                           text_auto=True)
                return figure_conditions

    with ui.nav_panel('Tables'):
        'Cost Table Data'


        @render.data_frame
        def prescription_data_table_cost():
            return render.DataGrid(prescribed_data.sort_values(['Gross Cost (£)'], ascending=False).round(2),
                                   filters=True, width='100%')


        'Count Table Data'


        @render.data_frame
        def prescription_data_table_count():
            return render.DataGrid(annual_sum_count.sort_values(['Total Quantity'], ascending=False).round(2),
                                   filters=True, width='100%')
