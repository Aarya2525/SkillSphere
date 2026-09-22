import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import {
  CertificateService,
  Certificate
} from '../../../core/services/certificate';

@Component({
  selector: 'app-certificate-verify',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './certificate-verify.html',
  styleUrl: './certificate-verify.scss'
})
export class CertificateVerifyComponent implements OnInit {
  private readonly certificateService = inject(CertificateService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  certificate: Certificate | null = null;

  loading = true;
  verified = false;
  errorMessage = '';

  ngOnInit(): void {
    const certificateId =
      this.route.snapshot.paramMap.get('certificateId');

    if (!certificateId) {
      this.loading = false;
      this.errorMessage = 'Certificate ID is missing.';
      return;
    }

    this.verifyCertificate(certificateId);
  }

  verifyCertificate(certificateId: string): void {
    this.loading = true;
    this.errorMessage = '';
    this.verified = false;

    this.certificateService.verifyCertificate(certificateId).subscribe({
      next: certificate => {
        this.certificate = certificate;
        this.verified = true;
        this.loading = false;
      },

      error: error => {
        console.error(
          'Certificate verification failed:',
          error
        );

        this.certificate = null;
        this.verified = false;
        this.loading = false;

        if (error.status === 404) {
          this.errorMessage =
            'This certificate could not be found. The certificate ID may be invalid.';
        } else {
          this.errorMessage =
            'Unable to verify this certificate. Please try again.';
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

  goToCertificates(): void {
    this.router.navigate(['/certificates']);
  }
} 