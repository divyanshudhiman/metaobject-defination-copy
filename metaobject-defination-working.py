import requests
import json

# Original store details (source)
original_url = "https://your-source-store.myshopify.com/admin/api/2025-01/graphql.json"
original_token = "shpat_your_source_token"

# New store details (target)
new_url = "https://your-target-store.myshopify.com/admin/api/2024-07/graphql.json"
new_token = "shpat_your_target_token"

# Fetch existing metaobject definitions from target store
def get_existing_definitions():
    existing_payload = {
        "query": """
        query getExistingMetaobjectDefinitions {
          metaobjectDefinitions(first: 250) {
            edges {
              node {
                type
                name
              }
            }
          }
        }
        """
    }
    
    existing_headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': new_token
    }
    
    response = requests.post(new_url, headers=existing_headers, json=existing_payload)
    if response.status_code == 200:
        data = response.json()
        existing_defs = data.get("data", {}).get("metaobjectDefinitions", {}).get("edges", [])
        return {edge['node']['type'] for edge in existing_defs}
    return set()

existing_types = get_existing_definitions()
print(f"\n📋 Found {len(existing_types)} existing definitions in target store")
if existing_types:
    print(f"   Existing types: {', '.join(sorted(existing_types))}")

# Fetch metaobject definitions from the original store
payload = {
  "query": """
  query getMetaobjectDefinitions {
  metaobjectDefinitions(first: 250) {
    edges {
      node {
        access {
          admin
          storefront
        }
        capabilities {
          onlineStore {
            data {
              canCreateRedirects
              urlHandle
            }
            enabled
          }
          publishable {
            enabled
          }
          renderable {
            enabled
            data {
              metaDescriptionKey
              metaTitleKey
            }
          }
          translatable {
            enabled
          }
        }
        description
        displayNameKey
        fieldDefinitions {
          description
          key
          name
          required
          type {
            category
            name
            supportedValidations {
              name
              type
            }
            valueType
            supportsDefinitionMigrations
          }
          validations {
            name
            type
            value
          }
        }
        hasThumbnailField
        id
        name
        type
        metaobjectsCount
      }
    }
  }
  }
  """
}

headers = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': original_token
}

response = requests.post(original_url, headers=headers, json=payload)
data = response.json()

if response.status_code != 200:
    print(f"Error fetching definitions: {response.status_code}")
    print(data)  # Print the error response
    exit()

print("Original Data:")  # Print the raw data from the source
print(json.dumps(data, indent=2))

definitions = data.get("data", {}).get("metaobjectDefinitions", {}).get("edges", [])

if not definitions:
    print("❌ No metaobject definitions found in source store")
else:
    print(f"\n📊 Found {len(definitions)} metaobject definitions to process\n" + "="*60)
    for edge in definitions:
        try:
            definition = edge['node']
            transformed_definition = {
                "name": definition["name"],
                "type": definition["type"],
                "description": definition.get("description"),  # Handle missing descriptions
                "displayNameKey": definition["displayNameKey"],
                "fieldDefinitions": []
            }

            field_definitions = definition.get("fieldDefinitions", [])
            for field_edge in field_definitions:
                field_type = field_edge["type"]["name"]
                # Skip metaobject reference fields as they need to be created after referenced objects exist
                if field_type not in ["list.metaobject_reference", "metaobject_reference"]:
                    # Filter validations to only include supported ones
                    filtered_validations = []
                    for validation in field_edge.get("validations", []):
                        # Only include validations that are supported by the field type
                        if validation.get("name") and validation.get("value") is not None:
                            filtered_validations.append({
                                "name": validation["name"],
                                "value": validation["value"]
                            })
                    
                    field_def = {
                        "key": field_edge["key"],
                        "type": field_type,
                        "name": field_edge["name"],
                        "required": field_edge["required"]
                    }
                    
                    # Only add description if it exists and is not empty
                    if field_edge.get("description"):
                        field_def["description"] = field_edge["description"]
                    
                    # Only add validations if there are any
                    if filtered_validations:
                        field_def["validations"] = filtered_validations
                    
                    transformed_definition["fieldDefinitions"].append(field_def)

            # Check if definition already exists in target store
            if definition['type'] in existing_types:
                print(f"\n⏭️ SKIPPED: '{definition['name']}' - Already exists in target store")
                continue
                
            # Skip if no compatible field definitions
            if not transformed_definition["fieldDefinitions"]:
                print(f"\n❌ SKIPPED: '{definition['name']}' - Contains only metaobject reference fields")
                print(f"   Original field types: {[f['type']['name'] for f in field_definitions]}")
                continue
                
            print(f"\n🔄 PROCESSING: '{definition['name']}' (Type: {definition['type']})")
            print(f"   Fields to create: {len(transformed_definition['fieldDefinitions'])}")
            for field in transformed_definition['fieldDefinitions']:
                validations_info = f" [{len(field.get('validations', []))} validations]" if field.get('validations') else ""
                print(f"   - {field['name']} ({field['type']}){validations_info}")

            # Create metaobject definition in the new store
            mutation = {
                "query": """
                mutation createMetaobjectDefinition($definition: MetaobjectDefinitionCreateInput!) {
                  metaobjectDefinitionCreate(definition: $definition) {
                    metaobjectDefinition {
                      name
                      type
                      description
                      displayNameKey
                      fieldDefinitions {
                        key
                        description
                        name
                        type {
                          name
                          category
                        }
                        required
                        validations {
                          name
                          value
                        }
                      }
                    }
                    userErrors {
                      field
                      message
                    }
                  }
                }
                """,
                "variables": {
                    "definition": transformed_definition
                }
            }

            headers = {
                'Content-Type': 'application/json',
                'X-Shopify-Access-Token': new_token
            }

            response = requests.post(new_url, headers=headers, json=mutation)
            result = response.json()

            # Only print full response if there are errors
            if result.get('errors') or result.get('data', {}).get('metaobjectDefinitionCreate', {}).get('userErrors'):
                print("\n📋 Full API Response:")
                print(json.dumps(result, indent=2))

            # Check for GraphQL errors or user errors
            if response.status_code != 200:
                print(f"\n❌ HTTP ERROR {response.status_code} for '{definition['name']}'")
                print(f"   Response: {result}")
            elif result.get('errors'):
                print(f"\n❌ GRAPHQL ERRORS for '{definition['name']}'")
                for error in result['errors']:
                    print(f"   - {error.get('message', 'Unknown error')}")
                    if error.get('locations'):
                        print(f"     Location: Line {error['locations'][0].get('line')}")
            elif result.get('data', {}).get('metaobjectDefinitionCreate', {}).get('userErrors'):
                user_errors = result['data']['metaobjectDefinitionCreate']['userErrors']
                print(f"\n❌ VALIDATION ERRORS for '{definition['name']}'")
                for error in user_errors:
                    field_info = f" (Field: {error.get('field', 'N/A')})" if error.get('field') else ""
                    print(f"   - {error.get('message', 'Unknown error')}{field_info}")
            else:
                created_def = result.get('data', {}).get('metaobjectDefinitionCreate', {}).get('metaobjectDefinition')
                if created_def:
                    print(f"\n✅ SUCCESS: '{created_def.get('name')}' created successfully")
                else:
                    print(f"\n❌ UNKNOWN FAILURE for '{definition['name']}' - No definition returned but no errors")

        except (KeyError, AttributeError) as e:
            print(f"\n❌ TRANSFORMATION ERROR for '{definition.get('name', 'Unknown')}'")
            print(f"   Error: {e}")
            print(f"   Missing field in definition structure")
            continue