import { CommonModule } from "@angular/common";
import { Component, EventEmitter, Input, Output, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { finalize } from "rxjs";

import { CopilotPreview } from "../../../core/interfaces/copilot.interface";
import { FilterTreeNode } from "../../../core/interfaces/filter-tree.interface";
import { CopilotService } from "../../../core/services/copilot.service";

@Component({
  selector: "app-copilot-panel",
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: "./copilot-panel.component.html",
  styleUrls: ["./copilot-panel.component.scss"],
})
export class CopilotPanelComponent {
  @Input() entity = "";
  @Output() applyFilter = new EventEmitter<FilterTreeNode>();

  private readonly copilotService = inject(CopilotService);

  prompt = "";
  preview: CopilotPreview | null = null;
  summary = "";
  errorMessage = "";
  loadingPreview = false;
  executing = false;

  get canPreview(): boolean {
    return (
      this.entity.trim().length > 0 &&
      this.prompt.trim().length > 0 &&
      !this.loadingPreview
    );
  }

  requestPreview(): void {
    if (!this.canPreview) return;
    this.errorMessage = "";
    this.summary = "";
    this.preview = null;
    this.loadingPreview = true;

    this.copilotService
      .preview({ entity: this.entity, prompt: this.prompt.trim() })
      .pipe(finalize(() => (this.loadingPreview = false)))
      .subscribe({
        next: (preview) => {
          this.preview = preview;
        },
        error: (error) => {
          this.errorMessage = this.errorText(error);
        },
      });
  }

  confirmPreview(): void {
    if (!this.preview || this.executing) return;
    this.executing = true;
    this.errorMessage = "";

    this.copilotService
      .execute(this.preview.confirmationToken)
      .pipe(finalize(() => (this.executing = false)))
      .subscribe({
        next: (response) => {
          this.summary = response.summary;
          if (this.preview) {
            this.applyFilter.emit(this.preview.filterTree);
          }
        },
        error: (error) => {
          this.errorMessage = this.errorText(error);
        },
      });
  }

  clear(): void {
    this.prompt = "";
    this.preview = null;
    this.summary = "";
    this.errorMessage = "";
  }

  private errorText(error: any): string {
    const detail = error?.error?.detail;
    if (typeof detail === "string") return detail;
    if (detail?.detail) return detail.detail;
    if (detail?.error) return detail.error;
    return error?.message || "Copilot request failed";
  }
}
