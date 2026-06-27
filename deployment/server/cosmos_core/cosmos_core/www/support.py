import frappe

def get_context(context):
    context.title = "CosmOS Support"
    context.no_sidebar = True
    context.no_cache = 1
    return context
