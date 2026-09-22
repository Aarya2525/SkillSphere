import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  CertificateService,
  Certificate
} from '../../../core/services/certificate';

@Component({
  selector: 'app-certificate-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './certificate-detail.html',
  styleUrl: './certificate-detail.scss'
})
export class CertificateDetailComponent implements OnInit {
  private readonly certificateService = inject(CertificateService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  certificate: Certificate | null = null;

  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    const certificateId = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!certificateId) {
      this.loading = false;
      this.errorMessage = 'Invalid certificate.';
      return;
    }

    this.loadCertificate(certificateId);
  }

  loadCertificate(id: number): void {
    this.loading = true;
    this.errorMessage = '';

    this.certificateService.getCertificate(id).subscribe({
      next: certificate => {
        this.certificate = certificate;
        this.loading = false;
      },

      error: error => {
        console.error(
          'Failed to load certificate:',
          error
        );

        this.loading = false;

        if (error.status === 404) {
          this.errorMessage = 'Certificate not found.';
        } else if (error.status === 403) {
          this.errorMessage =
            'You are not allowed to view this certificate.';
        } else if (error.status === 401) {
          this.errorMessage =
            'Your session has expired. Please log in again.';
        } else {
          this.errorMessage =
            'Unable to load the certificate. Please try again.';
        }
      }
    });
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  }

  goBack(): void {
    this.router.navigate(['/certificates']);
  }

  verifyCertificate(): void {
    if (!this.certificate) {
      return;
    }

    this.router.navigate([
      '/certificates',
      'verify',
      this.certificate.certificate_id
    ]);
  }

  printCertificate(): void {
    window.print();
  }
} 