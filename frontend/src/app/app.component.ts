import { Component } from "@angular/core";
import { RouterOutlet, RouterLink, RouterLinkActive } from "@angular/router";
import { CommonModule } from "@angular/common";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="app-layout">
      <header class="app-header">
        <div class="app-header-content">
          <h1 class="app-logo">🔍 Generic Filter System</h1>
          <nav class="app-nav">
            <a routerLink="/books" routerLinkActive="active" class="nav-link">
              📚 Books
            </a>
            <a routerLink="/authors" routerLinkActive="active" class="nav-link">
              ✍️ Authors
            </a>
          </nav>
        </div>
      </header>

      <main class="app-main">
        <router-outlet></router-outlet>
      </main>

      <footer class="app-footer">
        <p>Generic Filtering System - Portable Angular + FastAPI Solution</p>
      </footer>
    </div>
  `,
  styles: [
    `
      .app-layout {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
      }

      .app-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #fff;
        padding: 0 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      }

      .app-header-content {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 64px;
      }

      .app-logo {
        font-size: 20px;
        font-weight: 600;
        margin: 0;
      }

      .app-nav {
        display: flex;
        gap: 8px;
      }

      .nav-link {
        padding: 8px 16px;
        color: rgba(255, 255, 255, 0.8);
        text-decoration: none;
        border-radius: 6px;
        transition: all 0.2s ease;
        font-weight: 500;
      }

      .nav-link:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.1);
        text-decoration: none;
      }

      .nav-link.active {
        color: #fff;
        background: rgba(255, 255, 255, 0.2);
      }

      .app-main {
        flex: 1;
        padding: 24px;
        background: #f5f5f5;
      }

      .app-footer {
        background: #1a1a2e;
        color: rgba(255, 255, 255, 0.6);
        text-align: center;
        padding: 16px;
        font-size: 13px;
      }

      .app-footer p {
        margin: 0;
      }

      @media (max-width: 640px) {
        .app-header-content {
          flex-direction: column;
          height: auto;
          padding: 12px 0;
          gap: 12px;
        }

        .app-main {
          padding: 16px;
        }
      }
    `,
  ],
})
export class AppComponent {
  title = "Generic Filter System";
}
