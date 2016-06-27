#!/usr/bin/env python

from mimetypes import guess_type
import os
import subprocess

import requests
import json

from flask import Blueprint, abort, make_response, render_template, render_template_string
from jinja2 import Environment, FileSystemLoader

import app_config
import copytext
import oauth
from render_utils import load_graphic_config, make_context, render_with_context, smarty_filter

graphic = Blueprint('graphic', __name__)

@graphic.route('/<slug>/')
@oauth.oauth_required
def _graphics_detail(slug):
    """
    Renders a parent.html index with child.html embedded as iframe.
    """
    from flask import request

    graphic_path = '%s/%s' % (app_config.GRAPHICS_PATH, slug)

    # NOTE: Parent must load pym.js from same source as child to prevent version conflicts!
    context = make_context(asset_depth=2, root_path=graphic_path)
    context['slug'] = slug
    context['var_name'] = slug.replace('-', '_')

    template = 'parent.html'

    if not os.path.exists('%s/%s/js/lib/pym.js' % (app_config.GRAPHICS_PATH, slug)):
        template = 'parent_old.html'

    try:
        graphic_config = load_graphic_config(graphic_path)
        context.update(graphic_config.__dict__)

        if hasattr(graphic_config, 'COPY_GOOGLE_DOC_KEY') and graphic_config.COPY_GOOGLE_DOC_KEY:
            copy_path = '%s/%s.xlsx' % (graphic_path, slug)

            if request.args.get('refresh'):
                oauth.get_document(graphic_config.COPY_GOOGLE_DOC_KEY, copy_path)

            context['COPY'] = copytext.Copy(filename=copy_path)

        if hasattr(graphic_config, 'AIRTABLE_ENDPOINTS') and graphic_config.AIRTABLE_ENDPOINTS and request.args.get('refresh'):
            for airtable_endpoint in graphic_config.AIRTABLE_ENDPOINTS:
                copy_path = '%s/%s.json' % (graphic_path, airtable_endpoint['name'])

                results = []
                url = airtable_endpoint['url']

                print 'downloading %s' % airtable_endpoint['name']

                while True:
                    response = requests.get(url)
                    response.raise_for_status()

                    data = json.loads(response.text)

                    results = results + data['records']

                    if 'offset' in data:
                        offset = data['offset']
                        url = '%s&offset=%s' % (airtable_endpoint['url'], offset)
                    else:
                        break

                print '%s records found' % len(results)

                with open(copy_path, 'w+') as outfile:
                    json.dump(results, outfile)

    except IOError:
        pass

    return make_response(render_template(template, **context))

@graphic.route('/<slug>/child.html')
@oauth.oauth_required
def _graphics_child(slug):
    """
    Renders a child.html for embedding.
    """
    graphic_path = '%s/%s' % (app_config.GRAPHICS_PATH, slug)
    print graphic_path

    # Fallback for legacy projects w/o child templates
    if not os.path.exists('%s/child_template.html' % graphic_path):
        with open('%s/child.html' % graphic_path) as f:
            contents = f.read()

        return contents

    context = make_context(asset_depth=2, root_path=graphic_path)
    context['slug'] = slug
    context['var_name'] = slug.replace('-', '_')

    env = Environment(loader=FileSystemLoader(graphic_path))

    try:
        graphic_config = load_graphic_config(graphic_path)
        context.update(graphic_config.__dict__)

        if hasattr(graphic_config, 'JINJA_FILTER_FUNCTIONS'):
            for func in graphic_config.JINJA_FILTER_FUNCTIONS:
                env.filters[func.__name__] = func

        if hasattr(graphic_config, 'COPY_GOOGLE_DOC_KEY') and graphic_config.COPY_GOOGLE_DOC_KEY:
            copy_path = '%s/%s.xlsx' % (graphic_path, slug)

            context['COPY'] = copytext.Copy(filename=copy_path)

        if hasattr(graphic_config, 'AIRTABLE_ENDPOINTS') and graphic_config.AIRTABLE_ENDPOINTS:
            context['AIRTABLE_DATA'] = []

            results = []
            for airtable_endpoint in graphic_config.AIRTABLE_ENDPOINTS:
                copy_path = '%s/%s.json' % (graphic_path, airtable_endpoint['name'])

                with open(copy_path) as infile:
                    results = infile.read()

                context['AIRTABLE_DATA'].append({
                        'name': airtable_endpoint['name'],
                        'data': results
                    })
    except IOError:
        pass

    env.globals.update(render=render_with_context)
    env.filters['smarty'] = smarty_filter
    template = env.get_template('child_template.html')

    return make_response(template.render(**context))

# Render graphic LESS files on-demand
@graphic.route('/<slug>/css/<filename>.less')
def _graphic_less(slug, filename):
    """
    Compiles LESS for a graphic.
    """
    graphic_path = '%s/%s' % (app_config.GRAPHICS_PATH, slug)
    less_path = '%s/css/%s.less' % (graphic_path, filename)

    if not os.path.exists(less_path):
        abort(404)

    r = subprocess.check_output(['node_modules/less/bin/lessc', less_path])

    return make_response(r, 200, { 'Content-Type': 'text/css' })

# Serve arbitrary static files on-demand
@graphic.route('/<slug>/<path:path>')
def _static(slug, path):
    real_path = '%s/%s/%s' % (app_config.GRAPHICS_PATH, slug, path)

    try:
        with open(real_path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(real_path)[0] }
    except IOError:
        abort(404)
