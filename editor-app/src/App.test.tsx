import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the word count element on the sidebar', () => {
  render(<App />);
  const linkElement = screen.getByText(/0 sanaa/i);
  expect(linkElement).toBeInTheDocument();
});
