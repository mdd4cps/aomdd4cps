from flask import Flask, request, jsonify
import saxonche
import xml.dom.minidom as minidom

app = Flask(__name__)

@app.route('/transform', methods=['POST'])
def transform():
    try:
        # Parse the request data (XML and XSL)
        input_data = request.get_json()
        input_xml = input_data.get('inputXML')
        xsl_transformation = input_data.get('xslTransformation')
        print(input_data)

        if not input_xml or not xsl_transformation:
            return jsonify({'error': 'Both inputXML and xslTransformation are required.'}), 400

        print("XML Input: ", input_xml)
        print("XSL File: ", xsl_transformation)

        # Set up the Saxon processor
        with saxonche.PySaxonProcessor(license=False) as proc:
            # Parse the XML document
            document = proc.parse_xml(xml_text=input_xml)

            # Compile the XSLT stylesheet from the provided string
            xslt_proc = proc.new_xslt30_processor()
            executable = xslt_proc.compile_stylesheet(stylesheet_text=xsl_transformation)

            # Perform the transformation
            output = executable.transform_to_string(xdm_node=document)

        # Pretty-print the result
        pretty_result = minidom.parseString(output).toprettyxml()

        print("Transformation Result: ", pretty_result)
        return pretty_result, 200

    except Exception as e:
        print("Transformation error:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Set the port and host for Flask
    app.run(port=3000, host='0.0.0.0')

