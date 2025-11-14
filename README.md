# Outlook Email Viewer

A simple Vue 3 application to authenticate with Outlook and view emails, built with Vite.

## Features

- Login with Outlook (Microsoft OAuth)
- Fetch and display emails (subject, sender, body preview, attachments)
- Responsive UI

## Project Structure

```
.
├── .env
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── style.css
│   ├── assets/
│   └── components/
│       ├── MailViewer.vue
│       └── new.vue
└── public/
    └── vite.svg
```

## Getting Started

### Prerequisites

- Node.js (v16+ recommended)
- npm

### Installation

1. Clone the repository.
2. Install dependencies:

   ```sh
   npm install
   ```

3. Configure environment variables in `.env` (see sample in repo).

### Running Locally

Start the development server:

```sh
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Building for Production

```sh
npm run build
```

## Environment Variables

- `VITE_REST_API_ROOT`: Backend API root URL for authentication and email fetching.

## Vulnerabilities

There is **1 vulnerability** reported by npm. Run `npm audit` for details and consider updating dependencies.

## License

MIT

---

**Made with [Vue 3](https://vuejs.org/) & [Vite](https://vitejs.dev/)**