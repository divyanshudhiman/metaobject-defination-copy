# Shopify Metaobject Definition Migration Tool

A Python script to migrate metaobject definitions from one Shopify store to another using the Admin GraphQL API.

## Overview

This tool copies metaobject definitions (structure/schema only) from a source Shopify store to a target store. It automatically:
- Fetches existing definitions from the target store to avoid duplicates
- Filters out metaobject reference fields (which require referenced objects to exist first)
- Validates and creates compatible field definitions
- Provides detailed logging of the migration process

## Prerequisites

- Python 3.6+
- `requests` library
- Admin API access tokens for both stores
- GraphQL Admin API permissions on both stores

## Installation

1. Clone or download this repository
2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
3. Install required dependencies:
```bash
pip install requests
```

## Configuration

Edit the script variables at the top of `metaobject-defination-working.py`:

```python
# Original store details (source)
original_url = "https://your-source-store.myshopify.com/admin/api/2025-01/graphql.json"
original_token = "shpat_your_source_token"

# New store details (target)
new_url = "https://your-target-store.myshopify.com/admin/api/2024-07/graphql.json"
new_token = "shpat_your_target_token"
```

### Getting Access Tokens

1. Go to your Shopify Admin → Apps → Develop apps
2. Create a private app or use existing app
3. Enable Admin API access with these scopes:
   - `read_metaobjects`
   - `write_metaobjects`
4. Copy the Admin API access token

## Usage

Run the script:
```bash
python metaobject-defination-working.py
```

## What the Script Does

### 1. Checks Existing Definitions
- Queries target store for existing metaobject definitions
- Prevents duplicate creation attempts

### 2. Fetches Source Definitions
- Retrieves all metaobject definitions from source store
- Includes field definitions, validations, and metadata

### 3. Filters Compatible Fields
- Skips `metaobject_reference` and `list.metaobject_reference` fields
- These require referenced objects to exist first

### 4. Creates Definitions
- Transforms and creates compatible definitions in target store
- Preserves field validations where supported
- Provides detailed success/error reporting

## Output Examples

```
📋 Found 3 existing definitions in target store
   Existing types: product_specs, reviews, testimonials

📊 Found 5 metaobject definitions to process
============================================================

🔄 PROCESSING: 'Blog Posts' (Type: blog_post)
   Fields to create: 4
   - Title (single_line_text_field)
   - Content (multi_line_text_field) [1 validations]
   - Author (single_line_text_field)
   - Published Date (date_field)

⏭️ SKIPPED: 'Product Reviews' - Already exists in target store

❌ SKIPPED: 'Related Products' - Contains only metaobject reference fields
   Original field types: ['metaobject_reference', 'list.metaobject_reference']
```

## Limitations

- **Reference Fields**: Metaobject reference fields are skipped and need manual creation after all referenced objects exist
- **API Versions**: Ensure both stores use compatible API versions
- **Rate Limits**: Script doesn't handle Shopify API rate limits
- **Validation Compatibility**: Some field validations may not be compatible between stores

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify access tokens and API permissions
2. **GraphQL Errors**: Check API version compatibility
3. **Field Validation Errors**: Some validations may not be supported in target store

### Error Handling

The script provides detailed error messages including:
- HTTP status codes
- GraphQL errors
- User errors from Shopify API
- Full API responses for debugging

## Next Steps

After running this script:
1. Manually create metaobject reference fields
2. Migrate actual metaobject data (not just definitions)
3. Update any app code that references the metaobjects

## Security Notes

- Keep access tokens secure and never commit them to version control
- Use environment variables for production deployments
- Regularly rotate access tokens
- Limit API permissions to minimum required scopes