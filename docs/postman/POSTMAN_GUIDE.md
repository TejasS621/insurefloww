# InsureFlow Postman Collection Guide

## Overview
This is a comprehensive Postman collection for the InsureFlow project, including all API endpoints from both the Main Backend (port 8000) and Provider Backend (port 8001).

## Collection Structure

### Main Backend (Port 8000)
The main backend handles customer-facing operations and admin functions:

- **Health**: Service health checks
- **Authentication**: Customer OTP login, Admin login, and verification
- **Applications**: Create and manage insurance applications
- **Quotes**: Select and manage insurance quotes
- **Payments**: Initiate payment sessions
- **Policies**: View, download, and manage customer policies
- **Support Tickets**: Create and manage support tickets
- **Admin**: Broker management, ticket assignment, application review, policy status updates
- **Provider Sync Webhook**: Receive updates from provider backend

### Provider Backend (Port 8001)
The provider backend handles provider-specific operations:

- **Health**: Service health checks
- **Provider Authentication**: Provider admin login
- **Broker Management**: Register, list, and manage brokers
- **Quotes**: Generate quotes for broker requests
- **Policies**: Retrieve provider policies and documents
- **Payments**: Create payment sessions and mock payment pages
- **Webhooks**: Handle payment success events
- **Synchronization**: Dispatch provider synchronization events

## Environment Variables

Before using the collection, set up the following variables in your Postman environment:

### Base URLs
- `main_backend_url`: http://127.0.0.1:8000
- `provider_backend_url`: http://127.0.0.1:8001

### Authentication Tokens
- `customer_token`: JWT token obtained from customer OTP login
- `admin_token`: JWT token obtained from admin login
- `provider_admin_token`: JWT token obtained from provider admin login
- `broker_api_key`: API key for authenticated broker requests

### Resource IDs (populate as needed)
- `quote_id`: ID of a quote to select
- `transaction_reference`: Transaction reference for payments
- `policy_number`: Policy number to fetch
- `broker_code`: Broker code for operations
- `ticket_reference`: Ticket reference for admin operations
- `application_reference`: Application reference for admin operations
- `payment_reference`: Payment reference for webhooks

## Getting Started

### 1. Import the Collection
1. Open Postman
2. Click "Import" in the top left
3. Select the `InsureFlow_Complete_API_Collection.json` file
4. Click "Import"

### 2. Create an Environment
1. Click the gear icon (⚙️) in the top right
2. Click "Manage Environments"
3. Click "Create New Environment"
4. Name it "InsureFlow Dev" or similar
5. Add the variables listed above

### 3. Common Workflows

#### Customer Journey
1. **Request OTP**: POST /api/v1/auth/login/otp
   - Enter phone number: `+919876543210`
2. **Verify OTP**: POST /api/v1/auth/login/verify
   - Enter OTP code: `123456`
   - Copy `data.token.access_token` and save as `customer_token` variable
3. **Create Application**: POST /api/v1/applications
   - Fill in personal details
   - Note the transaction_reference
4. **Generate Quotes**: Use transaction_reference to get quotes (via provider backend)
5. **Select Quote**: POST /api/v1/quotes/select/{quote_id}
6. **Initiate Payment**: POST /api/v1/payments/initiate/{transaction_reference}

#### Admin Workflow
1. **Admin Login**: POST /api/v1/auth/admin/login
   - Email: `admin@insurefloww.com`
   - Password: `Admin@12345`
   - Copy token and save as `admin_token`
2. **Register Broker**: POST /api/v1/admin/brokers
3. **Manage Brokers**: Update status, rotate keys
4. **Review Applications**: PATCH /api/v1/admin/applications/{application_reference}/review

#### Provider Workflow
1. **Provider Admin Login**: POST /api/v1/auth/login
   - Email: `provider-admin@insurefloww.com`
   - Password: `Provider@12345`
   - Copy token and save as `provider_admin_token`
2. **Register Broker**: POST /api/v1/brokers/register
3. **Generate Quotes**: POST /api/v1/quotes/generate
4. **Create Payment Session**: POST /api/v1/payments/create-session

## Key Features

### Authentication
- **Customer Authentication**: OTP-based login for customers
- **Admin Authentication**: Email/password login for admins
- **Provider Authentication**: Email/password login for provider admins
- **Broker Authentication**: API key-based authentication for brokers

### API Response Format
All endpoints return responses in this format:
```json
{
  "message": "Success message",
  "data": {
    // Response data here
  }
}
```

## Error Handling

### Common Error Responses
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Insufficient permissions for the resource
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

## Notes

- JWT tokens expire after 60 minutes by default
- All timestamps are in UTC timezone
- Broker API keys should be stored securely
- Test credentials are for development only
- Mock payment pages are available at `/mock-razorpay/pay/{payment_reference}`

## Troubleshooting

### Token Expired
- Make a new login request to get a fresh token
- Update the corresponding token variable in your environment

### API Not Responding
- Ensure both backend services are running
- Check that ports 8000 and 8001 are accessible
- Verify MongoDB connection

### CORS Issues
- Ensure Postman is sending correct headers
- Check backend CORS configuration

## Additional Resources

- [Architecture Documentation](../architecture/DOCUMENTATION.md)
- [Implementation Plan](../architecture/IMPLEMENTATION_PLAN.md)
- [API Reference Docs](http://127.0.0.1:8000/docs) - Main Backend Swagger UI
- [Provider API Docs](http://127.0.0.1:8001/docs) - Provider Backend Swagger UI

## Support

For issues or questions about the API, please:
1. Check the service logs
2. Review the documentation
3. Create a support ticket using the API endpoints
