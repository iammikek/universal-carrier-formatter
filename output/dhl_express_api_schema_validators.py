"""
Auto-generated Pydantic validators from constraint extraction (Scenario 2).

How to use:
  1. Import this mixin and add it to your Pydantic model (mixin first so its validators run):
       from output.dhl_express_api_schema_validators import ConstraintValidatorsMixin
       from pydantic import BaseModel

       class MyRequest(ConstraintValidatorsMixin, BaseModel):
           ShipmentInfo_DHLCustomsInvoiceLanguageCode: str | None = None
           ...

  2. Your model field names must match the validator names. Validators use the exact
     field name from the docs (e.g. ShipmentInfo/DHLCustomsInvoiceLanguageCode becomes
     a validator for that key). Use the same name or alias in your model.

  3. Many validators are currently documentation-only (they return the value unchanged).
     Real validation is emitted when constraints include allowed_values, max_length,
     min_length, or pattern. Edit this file to add logic, or re-run extraction with
     constraints that have those keys.
"""

import re
from typing import Any

from pydantic import field_validator, model_validator

class ConstraintValidatorsMixin:
    """
    Pydantic v2 validators derived from extracted business rules.
    Include this mixin in your model to apply the constraints.
    """

    @field_validator('MessageTime', mode="before")
    @classmethod
    def _validate_MessageTime_0(cls, v: Any) -> Any:
        """Mandatory when Landed Cost is requested; format YYYY-MM-DD(T)hh:mm:ssGMTTIMEOFFSET"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(GMT[+-]\\d{2}:\\d{2})$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('MessageReference', mode="before")
    @classmethod
    def _validate_MessageReference_1(cls, v: Any) -> Any:
        """Mandatory when Landed Cost is requested; length between 28 and 36 characters"""
        if v is None:
            return v
        s = str(v)
        if len(s) < 28 or len(s) > 36:
            raise ValueError(f"'MessageReference' length must be between 28 and 36; got len={len(s)}")
        return v

    @field_validator('GetRateEstimates', mode="before")
    @classmethod
    def _validate_GetRateEstimates_2(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default Y; cannot be used with LandedCost"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'GetRateEstimates' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('GetDetailedRateBreakdown', mode="before")
    @classmethod
    def _validate_GetDetailedRateBreakdown_3(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N; cannot be used with LandedCost"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'GetDetailedRateBreakdown' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('IncludeAdditionalCurrencies', mode="before")
    @classmethod
    def _validate_IncludeAdditionalCurrencies_4(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'IncludeAdditionalCurrencies' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('DropOffType', mode="before")
    @classmethod
    def _validate_DropOffType_5(cls, v: Any) -> Any:
        """Mandatory; allowed values REGULAR_PICKUP or REQUEST_COURIER"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['REGULAR_PICKUP', 'REQUEST_COURIER']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'DropOffType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('NextBusinessDay', mode="before")
    @classmethod
    def _validate_NextBusinessDay_6(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'NextBusinessDay' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('ShipTimestamp', mode="before")
    @classmethod
    def _validate_ShipTimestamp_7(cls, v: Any) -> Any:
        """Mandatory; format YYYY-MM-DDTHH:MM:SSGMT+k; date must not be public holiday, Sunday or no pickup day"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}GMT[+-]\\d{2}:\\d{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('UnitOfMeasurement', mode="before")
    @classmethod
    def _validate_UnitOfMeasurement_8(cls, v: Any) -> Any:
        """Mandatory; allowed values SI (KG, CM) or SU (LB, IN)"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['SI', 'SU']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'UnitOfMeasurement' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('Content', mode="before")
    @classmethod
    def _validate_Content_9(cls, v: Any) -> Any:
        """Optional; allowed values DOCUMENTS or NON_DOCUMENTS"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['DOCUMENTS', 'NON_DOCUMENTS']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'Content' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('DeclaredValue', mode="before")
    @classmethod
    def _validate_DeclaredValue_10(cls, v: Any) -> Any:
        """Optional; decimal with max length 18 and 3 decimal places"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 18:
            raise ValueError(f"'DeclaredValue' length must be <= 18; got len={len(s)}")
        return v

    @field_validator('DeclaredValueCurrencyCode', mode="before")
    @classmethod
    def _validate_DeclaredValueCurrencyCode_11(cls, v: Any) -> Any:
        """Optional; 3 character currency code"""
        if v is None:
            return v
        if not re.fullmatch('^[A-Z]{3}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('PaymentInfo', mode="before")
    @classmethod
    def _validate_PaymentInfo_12(cls, v: Any) -> Any:
        """Mandatory for declarable shipments; allowed values are Incoterms codes"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['CFR', 'CIF', 'CIP', 'CPT', 'DAF', 'DDP', 'DDU', 'DAP', 'DAT', 'DEQ', 'DES', 'EXW', 'FAS', 'FCA', 'FOB', 'DPU']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'PaymentInfo' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('Account', mode="before")
    @classmethod
    def _validate_Account_13(cls, v: Any) -> Any:
        """Mandatory or Billing structure must be provided; 12 alphanumeric characters"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 12:
            raise ValueError(f"'Account' length must be <= 12; got len={len(s)}")
        return v

    @field_validator('PayerCountryCode', mode="before")
    @classmethod
    def _validate_PayerCountryCode_14(cls, v: Any) -> Any:
        """Optional; 2 character country code; mandatory if no account number provided and enabled by DHL"""
        if v is None:
            return v
        if not re.fullmatch('^[A-Z]{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('RequestValueAddedServicesAndRuleGroups', mode="before")
    @classmethod
    def _validate_RequestValueAddedServicesAndRuleGroups_15(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'RequestValueAddedServicesAndRuleGroups' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('ServiceType', mode="before")
    @classmethod
    def _validate_ServiceType_16(cls, v: Any) -> Any:
        """Mandatory; DHL Global Product Code; must be provided if Freight charges not provided in LandedCost"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 6:
            raise ValueError(f"'ServiceType' length must be <= 6; got len={len(s)}")
        return v

    @field_validator('NetworkTypeCode', mode="before")
    @classmethod
    def _validate_NetworkTypeCode_17(cls, v: Any) -> Any:
        """Optional; allowed values AL (all), DD (Economy Select), TD (Time Definite); default AL"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['AL', 'DD', 'TD']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'NetworkTypeCode' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('CustomerAgreementInd', mode="before")
    @classmethod
    def _validate_CustomerAgreementInd_18(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default Y"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'CustomerAgreementInd' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('ValidateReadyTime', mode="before")
    @classmethod
    def _validate_ValidateReadyTime_19(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'ValidateReadyTime' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('StrictValidation', mode="before")
    @classmethod
    def _validate_StrictValidation_20(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'StrictValidation' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('RequestEstimatedDeliveryDate', mode="before")
    @classmethod
    def _validate_RequestEstimatedDeliveryDate_21(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default Y for RateRequest, N for ShipmentRequest"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'RequestEstimatedDeliveryDate' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('EstimatedDeliveryDateType', mode="before")
    @classmethod
    def _validate_EstimatedDeliveryDateType_22(cls, v: Any) -> Any:
        """Optional; allowed values QDDF (fastest transit time) or QDDC (DHL service commitment); default QDDF"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['QDDF', 'QDDC']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'EstimatedDeliveryDateType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('Packages', mode="before")
    @classmethod
    def _validate_Packages_23(cls, v: Any) -> Any:
        """Mandatory; minimum 1 package, maximum 999; each package must have Weight > 0.1kg; Weight and Dimensions required"""
        return v

    @field_validator('ShipmentIdentificationNumber', mode="before")
    @classmethod
    def _validate_ShipmentIdentificationNumber_24(cls, v: Any) -> Any:
        """Optional; max length 35; only used if UseOwnShipmentIdentificationNumber is Y and feature enabled"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 35:
            raise ValueError(f"'ShipmentIdentificationNumber' length must be <= 35; got len={len(s)}")
        return v

    @field_validator('UseOwnShipmentIdentificationNumber', mode="before")
    @classmethod
    def _validate_UseOwnShipmentIdentificationNumber_25(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N; enables use of own AWB number"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'UseOwnShipmentIdentificationNumber' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelType', mode="before")
    @classmethod
    def _validate_LabelType_26(cls, v: Any) -> Any:
        """Optional; allowed values PDF, ZPL, EPL, LP2; default PDF"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['PDF', 'ZPL', 'EPL', 'LP2']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LabelType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelTemplate', mode="before")
    @classmethod
    def _validate_LabelTemplate_27(cls, v: Any) -> Any:
        """Optional; any valid DHL Express label template; default ECOM26_84_001"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 25:
            raise ValueError(f"'LabelTemplate' length must be <= 25; got len={len(s)}")
        return v

    @field_validator('ArchiveLabelTemplate', mode="before")
    @classmethod
    def _validate_ArchiveLabelTemplate_28(cls, v: Any) -> Any:
        """Optional; any valid DHL Express archive label template; default ARCH_8x4"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 25:
            raise ValueError(f"'ArchiveLabelTemplate' length must be <= 25; got len={len(s)}")
        return v

    @field_validator('QRCodeTemplate', mode="before")
    @classmethod
    def _validate_QRCodeTemplate_29(cls, v: Any) -> Any:
        """Optional; QR Code template name; default QR_1_00_LL_PNG_001"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 25:
            raise ValueError(f"'QRCodeTemplate' length must be <= 25; got len={len(s)}")
        return v

    @field_validator('QRCodeImageFormat', mode="before")
    @classmethod
    def _validate_QRCodeImageFormat_30(cls, v: Any) -> Any:
        """Optional; QR Code image format; default PNG"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['PNG']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'QRCodeImageFormat' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('CustomsInvoiceTemplate', mode="before")
    @classmethod
    def _validate_CustomsInvoiceTemplate_31(cls, v: Any) -> Any:
        """Optional; customs invoice template name; default COMMERCIAL_INVOICE_P_10; see documentation for allowed values"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['COMMERCIAL_INVOICE_04', 'COMMERCIAL_INVOICE_L_10', 'COMMERCIAL_INVOICE_P_10', 'RET_COM_INVOICE_A4_01', 'RETURNS_INVOICE']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'CustomsInvoiceTemplate' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('ShipmentReceiptTemplate', mode="before")
    @classmethod
    def _validate_ShipmentReceiptTemplate_32(cls, v: Any) -> Any:
        """Optional; shipment receipt template name; default SHIPRCPT_EN_001"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['SHIP_RECPT_A4_RU_002', 'SHIPRCPT_EN_001']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'ShipmentReceiptTemplate' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('RequestDHLCustomsInvoice', mode="before")
    @classmethod
    def _validate_RequestDHLCustomsInvoice_33(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'RequestDHLCustomsInvoice' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('DHLCustomsInvoiceLanguageCode', mode="before")
    @classmethod
    def _validate_DHLCustomsInvoiceLanguageCode_34(cls, v: Any) -> Any:
        """Optional; 3 character language code; default eng; allowed values include eng, dan, ita, etc."""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['eng', 'dan', 'ita', 'bul', 'cze', 'ger', 'gre', 'est', 'fin', 'fre', 'hun', 'ice', 'lit', 'lav', 'dut', 'nno', 'pol', 'por', 'rum', 'rus', 'slv', 'slo', 'spa', 'heb', 'jpn', 'kor', 'mac', 'nor', 'srd', 'tha', 'tur', 'twi', 'ukr', 'ara', 'bos', 'geo', 'vie']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'DHLCustomsInvoiceLanguageCode' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('DHLCustomsInvoiceLanguageCountryCode', mode="before")
    @classmethod
    def _validate_DHLCustomsInvoiceLanguageCountryCode_35(cls, v: Any) -> Any:
        """Optional; 2 character ISO country code"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 2:
            raise ValueError(f"'DHLCustomsInvoiceLanguageCountryCode' length must be <= 2; got len={len(s)}")
        return v

    @field_validator('DHLCustomsInvoiceType', mode="before")
    @classmethod
    def _validate_DHLCustomsInvoiceType_36(cls, v: Any) -> Any:
        """Optional; allowed values COMMERCIAL_INVOICE, PROFORMA_INVOICE, RETURNS_INVOICE; default COMMERCIAL_INVOICE"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['COMMERCIAL_INVOICE', 'PROFORMA_INVOICE', 'RETURNS_INVOICE']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'DHLCustomsInvoiceType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelOptions/CustomerLogo/LogoImage', mode="before")
    @classmethod
    def _validate_LabelOptions_CustomerLogo_LogoImage_37(cls, v: Any) -> Any:
        """Optional; base64 encoded image; max size 1MB; supported formats RGB and B&W"""
        return v

    @field_validator('LabelOptions/CustomerLogo/LogoImageFormat', mode="before")
    @classmethod
    def _validate_LabelOptions_CustomerLogo_LogoImageFormat_38(cls, v: Any) -> Any:
        """Optional; allowed values GIF, JPEG, JPG, PNG"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['GIF', 'JPEG', 'JPG', 'PNG']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LabelOptions/CustomerLogo/LogoImageFormat' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelOptions/CustomerBarcode/BarcodeType', mode="before")
    @classmethod
    def _validate_LabelOptions_CustomerBarcode_BarcodeType_39(cls, v: Any) -> Any:
        """Optional; allowed values 39, 93, 128; mandatory if BarcodeContent or TextBelowBarcode provided"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['39', '93', '128']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LabelOptions/CustomerBarcode/BarcodeType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelOptions/CustomerBarcode/BarcodeContent', mode="before")
    @classmethod
    def _validate_LabelOptions_CustomerBarcode_BarcodeContent_40(cls, v: Any) -> Any:
        """Optional; string; mandatory if BarcodeType provided"""
        return v

    @field_validator('LabelOptions/CustomerBarcode/TextBelowBarcode', mode="before")
    @classmethod
    def _validate_LabelOptions_CustomerBarcode_TextBelowBarcode_41(cls, v: Any) -> Any:
        """Optional; string; mandatory if BarcodeType provided"""
        return v

    @field_validator('LabelOptions/DetachOptions/AllInOnePDF', mode="before")
    @classmethod
    def _validate_LabelOptions_DetachOptions_AllInOnePDF_42(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N; only allowed for PDF output types"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LabelOptions/DetachOptions/AllInOnePDF' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelOptions/DetachOptions/SplitShipmentReceiptAndCustomsInvoice', mode="before")
    @classmethod
    def _validate_LabelOptions_DetachOptions_SplitShipmentReceiptA_43(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LabelOptions/DetachOptions/SplitShipmentReceiptAndCustomsInvoice' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('LabelOptions/DetachOptions/SplitTransportLabelAndWaybillDocument', mode="before")
    @classmethod
    def _validate_LabelOptions_DetachOptions_SplitTransportLabelAn_44(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LabelOptions/DetachOptions/SplitTransportLabelAndWaybillDocument' must be one of {allowed}; got {v!r}")
        return v

    @model_validator(mode="after")
    def _validate_LabelOptions_DetachOptions_SplitLabelsByPieces_45(self) -> Any:
        """Optional; allowed values Y or N; default N; must be Y if LinkLabelsByPieces is Y (condition: LinkLabelsByPieces == 'Y')"""
        return self

    @field_validator('LinkLabelsByPieces', mode="before")
    @classmethod
    def _validate_LinkLabelsByPieces_46(cls, v: Any) -> Any:
        """Optional; allowed values Y or N; default N; if Y, SplitLabelsByPieces must be Y and AllInOnePDF must not be Y"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['Y', 'N']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'LinkLabelsByPieces' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('ShipmentTimestamp', mode="before")
    @classmethod
    def _validate_ShipmentTimestamp_47(cls, v: Any) -> Any:
        """Mandatory; format YYYY-MM-DDTHH:MM:SSGMT+k; date must not be public holiday, Sunday or no pickup day"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}GMT[+-]\\d{2}:\\d{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @model_validator(mode="after")
    def _validate_PickupLocationCloseTime_48(self) -> Any:
        """Optional; format HH:mm 24-hour; must be later than PickupTimestamp if provided (condition: DropOffType == 'REQUEST_COURIER')"""
        return self

    @model_validator(mode="after")
    def _validate_SpecialPickupInstruction_49(self) -> Any:
        """Optional; max length 75; only valid if DropOffType == REQUEST_COURIER (condition: DropOffType == 'REQUEST_COURIER')"""
        return self

    @model_validator(mode="after")
    def _validate_PickupLocation_50(self) -> Any:
        """Optional; max length 80; only valid if DropOffType == REQUEST_COURIER (condition: DropOffType == 'REQUEST_COURIER')"""
        return self

    @field_validator('PickupLocationType', mode="before")
    @classmethod
    def _validate_PickupLocationType_51(cls, v: Any) -> Any:
        """Optional; allowed values B or R"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['B', 'R']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'PickupLocationType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('Billing/ShipperAccountNumber', mode="before")
    @classmethod
    def _validate_Billing_ShipperAccountNumber_52(cls, v: Any) -> Any:
        """Mandatory; 9 alphanumeric characters"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 9:
            raise ValueError(f"'Billing/ShipperAccountNumber' length must be <= 9; got len={len(s)}")
        return v

    @field_validator('Billing/ShippingPaymentType', mode="before")
    @classmethod
    def _validate_Billing_ShippingPaymentType_53(cls, v: Any) -> Any:
        """Mandatory; allowed values S, R, T; if R or T, BillingAccountNumber is mandatory"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['S', 'R', 'T']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'Billing/ShippingPaymentType' must be one of {allowed}; got {v!r}")
        return v

    @model_validator(mode="after")
    def _validate_Billing_BillingAccountNumber_54(self) -> Any:
        """Optional; 9 alphanumeric characters; mandatory if ShippingPaymentType is R or T (condition: ShippingPaymentType in ['R', 'T'])"""
        return self

    @field_validator('PickupTimestamp', mode="before")
    @classmethod
    def _validate_PickupTimestamp_55(cls, v: Any) -> Any:
        """Mandatory; format YYYY-MM-DDTHH:MM:SSGMT+k; cannot be in the past or more than 28 days in future"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}GMT[+-]\\d{2}:\\d{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('Packages', mode="before")
    @classmethod
    def _validate_Packages_56(cls, v: Any) -> Any:
        """Mandatory; minimum 1 package, maximum 999; each package must have Weight > 0; Weight and Dimensions required"""
        return v

    @field_validator('ShipmentIdentificationNumber', mode="before")
    @classmethod
    def _validate_ShipmentIdentificationNumber_57(cls, v: Any) -> Any:
        """Optional; max length 35; corresponds to waybill number"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 35:
            raise ValueError(f"'ShipmentIdentificationNumber' length must be <= 35; got len={len(s)}")
        return v

    @field_validator('RegistrationNumbers/NumberTypeCode', mode="before")
    @classmethod
    def _validate_RegistrationNumbers_NumberTypeCode_58(cls, v: Any) -> Any:
        """Mandatory; allowed values include CNP, DAN, DTF, DUN, EIN, EOR, FED, FTZ, SDT, SSN, STA, VAT, NID, PAS, MID, IMS, EIC, etc."""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['CNP', 'DAN', 'DTF', 'DUN', 'EIN', 'EOR', 'FED', 'FTZ', 'SDT', 'SSN', 'STA', 'VAT', 'NID', 'PAS', 'MID', 'IMS', 'EIC', 'DLI', 'PAS', 'CHA', 'CPA', 'POA', 'BEX', 'DGD', 'IPA', 'T2M', 'TAD', 'TCS', 'ROD', 'EXL', 'HWB', 'ELP']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'RegistrationNumbers/NumberTypeCode' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('RegistrationNumbers/NumberIssuerCountryCode', mode="before")
    @classmethod
    def _validate_RegistrationNumbers_NumberIssuerCountryCode_59(cls, v: Any) -> Any:
        """Mandatory; 2 character ISO country code"""
        if v is None:
            return v
        if not re.fullmatch('^[A-Z]{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('InvoiceDate', mode="before")
    @classmethod
    def _validate_InvoiceDate_60(cls, v: Any) -> Any:
        """Mandatory for declarable shipments; format YYYY-MM-DD; drives exchange rate calculation"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @model_validator(mode="after")
    def _validate_InvoiceNumber_61(self) -> Any:
        """Mandatory when RequestDHLCustomsInvoice = Y; min length 1; max length 35 (condition: RequestDHLCustomsInvoice == 'Y')"""
        return self

    @model_validator(mode="after")
    def _validate_ExportDeclaration_62(self) -> Any:
        """Mandatory if shipment is dutiable; optional if ServiceType = PM; must not be provided with ServiceType = PM (condition: Content == 'NON_DOCUMENTS' or ServiceType != 'PM')"""
        return self

    @field_validator('ExportLineItems', mode="before")
    @classmethod
    def _validate_ExportLineItems_63(cls, v: Any) -> Any:
        """Mandatory; 1 to 999 items; each item requires ItemNumber, Quantity, QuantityUnitOfMeasurement, ItemDescription, UnitPrice, NetWeight or GrossWeight, ManufacturingCountryCode"""
        return v

    @field_validator('OtherCharges/ChargeType', mode="before")
    @classmethod
    def _validate_OtherCharges_ChargeType_64(cls, v: Any) -> Any:
        """Mandatory; allowed values ADMIN, DELIV, DOCUM, EXPED, EXCHA, FRCST, SSRGE, LOGST, SOTHR, SPKGN, PICUP, HRCRG, VATCR, INSCH, REVCH"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['ADMIN', 'DELIV', 'DOCUM', 'EXPED', 'EXCHA', 'FRCST', 'SSRGE', 'LOGST', 'SOTHR', 'SPKGN', 'PICUP', 'HRCRG', 'VATCR', 'INSCH', 'REVCH']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'OtherCharges/ChargeType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('OtherCharges/ChargeValue', mode="before")
    @classmethod
    def _validate_OtherCharges_ChargeValue_65(cls, v: Any) -> Any:
        """Mandatory; decimal; value must be > 0"""
        return v

    @field_validator('InvoiceReferences/InvoiceReferenceType', mode="before")
    @classmethod
    def _validate_InvoiceReferences_InvoiceReferenceType_66(cls, v: Any) -> Any:
        """Mandatory; allowed values ACL, CID, CN, CU, ITN, MRN, UCN, OID, PON, RMA, AAM, ABT, ADA, AES, AFD, ANT, BKN, BOL, CDN, COD, DSC, FF, FN, FTR, HWB, IBC, IPP, LLR, MAB, MWB, OBC, PD, PRN, RTL, SID, SS, SWN"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['ACL', 'CID', 'CN', 'CU', 'ITN', 'MRN', 'UCN', 'OID', 'PON', 'RMA', 'AAM', 'ABT', 'ADA', 'AES', 'AFD', 'ANT', 'BKN', 'BOL', 'CDN', 'COD', 'DSC', 'FF', 'FN', 'FTR', 'HWB', 'IBC', 'IPP', 'LLR', 'MAB', 'MWB', 'OBC', 'PD', 'PRN', 'RTL', 'SID', 'SS', 'SWN']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'InvoiceReferences/InvoiceReferenceType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('InvoiceReferences/InvoiceReferenceNumber', mode="before")
    @classmethod
    def _validate_InvoiceReferences_InvoiceReferenceNumber_67(cls, v: Any) -> Any:
        """Mandatory; max length 35; recommended max length 20 for Order Number"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 35:
            raise ValueError(f"'InvoiceReferences/InvoiceReferenceNumber' length must be <= 35; got len={len(s)}")
        return v

    @field_validator('CustomsDocumentType', mode="before")
    @classmethod
    def _validate_CustomsDocumentType_68(cls, v: Any) -> Any:
        """Mandatory; allowed values include 972, AHC, ATA, ATR, CHD, CHP, CIT, COO, DEX, EU1, EU2, EUS, FMA, PHY, VET, VEX, CRL, CSD, PCH, CI2, CIV, DOV, INV, PFI, ALC, HLC, JLC, LIC, LNP, PLI, DLI, NID, PAS, CHA, CPA, POA, BEX, DGD, IPA, T2M, TAD, TCS, ROD, EXL, HWB, ELP"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['972', 'AHC', 'ATA', 'ATR', 'CHD', 'CHP', 'CIT', 'COO', 'DEX', 'EU1', 'EU2', 'EUS', 'FMA', 'PHY', 'VET', 'VEX', 'CRL', 'CSD', 'PCH', 'CI2', 'CIV', 'DOV', 'INV', 'PFI', 'ALC', 'HLC', 'JLC', 'LIC', 'LNP', 'PLI', 'DLI', 'NID', 'PAS', 'CHA', 'CPA', 'POA', 'BEX', 'DGD', 'IPA', 'T2M', 'TAD', 'TCS', 'ROD', 'EXL', 'HWB', 'ELP']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'CustomsDocumentType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('CustomsDocumentID', mode="before")
    @classmethod
    def _validate_CustomsDocumentID_69(cls, v: Any) -> Any:
        """Mandatory; max length 35; min length 1"""
        if v is None:
            return v
        s = str(v)
        if len(s) < 1 or len(s) > 35:
            raise ValueError(f"'CustomsDocumentID' length must be between 1 and 35; got len={len(s)}")
        return v

    @field_validator('RemarkDescription', mode="before")
    @classmethod
    def _validate_RemarkDescription_70(cls, v: Any) -> Any:
        """Mandatory; max 3 occurrences; max length 45 for COMMERCIAL_INVOICE_L_10 and COMMERCIAL_INVOICE_P_10; max length 20 for COMMERCIAL_INVOICE_04"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 45:
            raise ValueError(f"'RemarkDescription' length must be <= 45; got len={len(s)}")
        return v

    @field_validator('InvoiceSignatureDetails/SignatureName', mode="before")
    @classmethod
    def _validate_InvoiceSignatureDetails_SignatureName_71(cls, v: Any) -> Any:
        """Optional; max length 35"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 35:
            raise ValueError(f"'InvoiceSignatureDetails/SignatureName' length must be <= 35; got len={len(s)}")
        return v

    @field_validator('InvoiceSignatureDetails/SignatureTitle', mode="before")
    @classmethod
    def _validate_InvoiceSignatureDetails_SignatureTitle_72(cls, v: Any) -> Any:
        """Optional; max length 35"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 35:
            raise ValueError(f"'InvoiceSignatureDetails/SignatureTitle' length must be <= 35; got len={len(s)}")
        return v

    @field_validator('InvoiceSignatureDetails/SignatureImage', mode="before")
    @classmethod
    def _validate_InvoiceSignatureDetails_SignatureImage_73(cls, v: Any) -> Any:
        """Optional; base64 encoded image; max size 1MB; valid formats PNG, GIF, JPEG, JPG"""
        return v

    @field_validator('InvoiceDeclarationText', mode="before")
    @classmethod
    def _validate_InvoiceDeclarationText_74(cls, v: Any) -> Any:
        """Optional; max 3 occurrences; max length 700; only printed for COMMERCIAL_INVOICE_04"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 700:
            raise ValueError(f"'InvoiceDeclarationText' length must be <= 700; got len={len(s)}")
        return v

    @field_validator('CustomerDataTextEntry', mode="before")
    @classmethod
    def _validate_CustomerDataTextEntry_75(cls, v: Any) -> Any:
        """Optional; max 6 occurrences; max length 45; only printed for COMMERCIAL_INVOICE_04"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 45:
            raise ValueError(f"'CustomerDataTextEntry' length must be <= 45; got len={len(s)}")
        return v

    @field_validator('RegistrationNumber/NumberTypeCode', mode="before")
    @classmethod
    def _validate_RegistrationNumber_NumberTypeCode_76(cls, v: Any) -> Any:
        """Mandatory; allowed values include CNP, DAN, DTF, DUN, EIN, EOR, FED, FTZ, SDT, SSN, STA, VAT, NID, PAS, MID, IMS, EIC, etc.; not all codes applicable for all countries and roles"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['CNP', 'DAN', 'DTF', 'DUN', 'EIN', 'EOR', 'FED', 'FTZ', 'SDT', 'SSN', 'STA', 'VAT', 'NID', 'PAS', 'MID', 'IMS', 'EIC', 'DLI', 'CHA', 'CPA', 'POA', 'BEX', 'DGD', 'IPA', 'T2M', 'TAD', 'TCS', 'ROD', 'EXL', 'HWB', 'ELP']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'RegistrationNumber/NumberTypeCode' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('RegistrationNumber/NumberIssuerCountryCode', mode="before")
    @classmethod
    def _validate_RegistrationNumber_NumberIssuerCountryCode_77(cls, v: Any) -> Any:
        """Mandatory; 2 character ISO country code"""
        if v is None:
            return v
        if not re.fullmatch('^[A-Z]{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('DangerousGoods/Content/ContentID', mode="before")
    @classmethod
    def _validate_DangerousGoods_Content_ContentID_78(cls, v: Any) -> Any:
        """Mandatory; valid DHL Express Dangerous Goods content ID; contact DHL representative for codes"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 3:
            raise ValueError(f"'DangerousGoods/Content/ContentID' length must be <= 3; got len={len(s)}")
        return v

    @field_validator('DangerousGoods/Content/CustomDescription', mode="before")
    @classmethod
    def _validate_DangerousGoods_Content_CustomDescription_79(cls, v: Any) -> Any:
        """Optional; max length 200; multiple descriptions concatenated with max combined length 200"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 200:
            raise ValueError(f"'DangerousGoods/Content/CustomDescription' length must be <= 200; got len={len(s)}")
        return v

    @field_validator('DangerousGoods/Content/DryIceTotalNetWeight', mode="before")
    @classmethod
    def _validate_DangerousGoods_Content_DryIceTotalNetWeight_80(cls, v: Any) -> Any:
        """Optional; numeric string up to 7 characters; format e.g. 1000.00 or 1000,00"""
        if v is None:
            return v
        if not re.fullmatch('^[0-9]+([.][0-9]+)?$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('DangerousGoods/Content/UNCodes/UNCode', mode="before")
    @classmethod
    def _validate_DangerousGoods_Content_UNCodes_UNCode_81(cls, v: Any) -> Any:
        """Optional; max 10 UN Numbers per Dangerous Goods Content; max length 10"""
        return v

    @field_validator('ShipmentNotifications/ShipmentNotification', mode="before")
    @classmethod
    def _validate_ShipmentNotifications_ShipmentNotification_82(cls, v: Any) -> Any:
        """Optional; max 5 occurrences; NotificationMethod mandatory with value EMAIL; EmailAddress optional but must be valid email if provided; LanguageCode optional with allowed values eng, dan, ita, zho, chi, etc.; LanguageCountryCode optional with allowed values CH, GB, US, DK, IT"""
        return v

    @field_validator('TrackingRequest/MessageTime', mode="before")
    @classmethod
    def _validate_TrackingRequest_MessageTime_83(cls, v: Any) -> Any:
        """Mandatory; format YYYY-MM-DD(T)hh:mm:ssZ"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('TrackingRequest/MessageReference', mode="before")
    @classmethod
    def _validate_TrackingRequest_MessageReference_84(cls, v: Any) -> Any:
        """Mandatory; length between 28 and 32 characters"""
        if v is None:
            return v
        s = str(v)
        if len(s) < 28 or len(s) > 32:
            raise ValueError(f"'TrackingRequest/MessageReference' length must be between 28 and 32; got len={len(s)}")
        return v

    @field_validator('TrackingRequest/LanguageCode', mode="before")
    @classmethod
    def _validate_TrackingRequest_LanguageCode_85(cls, v: Any) -> Any:
        """Mandatory if LanguageScriptCode or LanguageCountryCode provided; allowed values include eng, bak, bul, cze, dan, ger, ewe, gre, spa, est, fin, fre, heb, hrv, hun, ind, ita, jpn, kor, lit, lav, mac, dut, nor, pol, por, rum, rus, srd, slo, slv, alb, srp, swe, chi, tha, tur, twi, ukr, ice, ara, bos, geo, vie"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['eng', 'bak', 'bul', 'cze', 'dan', 'ger', 'ewe', 'gre', 'spa', 'est', 'fin', 'fre', 'heb', 'hrv', 'hun', 'ind', 'ita', 'jpn', 'kor', 'lit', 'lav', 'mac', 'dut', 'nor', 'pol', 'por', 'rum', 'rus', 'srd', 'slo', 'slv', 'alb', 'srp', 'swe', 'chi', 'tha', 'tur', 'twi', 'ukr', 'ice', 'ara', 'bos', 'geo', 'vie']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/LanguageCode' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/LanguageScriptCode', mode="before")
    @classmethod
    def _validate_TrackingRequest_LanguageScriptCode_86(cls, v: Any) -> Any:
        """Optional; 4 character string"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 4:
            raise ValueError(f"'TrackingRequest/LanguageScriptCode' length must be <= 4; got len={len(s)}")
        return v

    @field_validator('TrackingRequest/LanguageCountryCode', mode="before")
    @classmethod
    def _validate_TrackingRequest_LanguageCountryCode_87(cls, v: Any) -> Any:
        """Optional; 2 character string"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 2:
            raise ValueError(f"'TrackingRequest/LanguageCountryCode' length must be <= 2; got len={len(s)}")
        return v

    @field_validator('TrackingRequest/AWBNumber', mode="before")
    @classmethod
    def _validate_TrackingRequest_AWBNumber_88(cls, v: Any) -> Any:
        """Mandatory; 1 to 100 DHL Waybill numbers; each max length 11 characters"""
        return v

    @field_validator('TrackingRequest/LPNumber', mode="before")
    @classmethod
    def _validate_TrackingRequest_LPNumber_89(cls, v: Any) -> Any:
        """Optional; 1 to 100 DHL Piece IDs; each max length 35 characters"""
        return v

    @field_validator('TrackingRequest/ReferenceQuery/ShipperAccountNumber', mode="before")
    @classmethod
    def _validate_TrackingRequest_ReferenceQuery_ShipperAccountNum_90(cls, v: Any) -> Any:
        """Mandatory if ReferenceQuery used; 12 alphanumeric characters"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 12:
            raise ValueError(f"'TrackingRequest/ReferenceQuery/ShipperAccountNumber' length must be <= 12; got len={len(s)}")
        return v

    @field_validator('TrackingRequest/ReferenceQuery/ShipmentReferences/ShipmentReference', mode="before")
    @classmethod
    def _validate_TrackingRequest_ReferenceQuery_ShipmentReference_91(cls, v: Any) -> Any:
        """Mandatory if ReferenceQuery used; max length 35"""
        if v is None:
            return v
        s = str(v)
        if len(s) > 35:
            raise ValueError(f"'TrackingRequest/ReferenceQuery/ShipmentReferences/ShipmentReference' length must be <= 35; got len={len(s)}")
        return v

    @field_validator('TrackingRequest/ReferenceQuery/ShipmentReferences/ShipmentReferenceType', mode="before")
    @classmethod
    def _validate_TrackingRequest_ReferenceQuery_ShipmentReference_92(cls, v: Any) -> Any:
        """Optional; allowed value CU"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['CU']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/ReferenceQuery/ShipmentReferences/ShipmentReferenceType' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/ReferenceQuery/ShipmentDateRange/From', mode="before")
    @classmethod
    def _validate_TrackingRequest_ReferenceQuery_ShipmentDateRange_93(cls, v: Any) -> Any:
        """Mandatory if ReferenceQuery used; date format YYYYMM-DD"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('TrackingRequest/ReferenceQuery/ShipmentDateRange/To', mode="before")
    @classmethod
    def _validate_TrackingRequest_ReferenceQuery_ShipmentDateRange_94(cls, v: Any) -> Any:
        """Mandatory if ReferenceQuery used; date format YYYYMM-DD"""
        if v is None:
            return v
        if not re.fullmatch('^\\d{4}-\\d{2}-\\d{2}$', str(v)):
            raise ValueError(f"{field!r} must match pattern {repr(pattern)}; got {v!r}")
        return v

    @field_validator('TrackingRequest/LevelOfDetails', mode="before")
    @classmethod
    def _validate_TrackingRequest_LevelOfDetails_95(cls, v: Any) -> Any:
        """Mandatory; allowed values ALL_CHECKPOINTS, LAST_CHECKPOINT_ONLY, ADVANCE_SHIPMENT, BBX_CHILDREN, SHIPMENT_DETAILS_ONLY"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['ALL_CHECKPOINTS', 'LAST_CHECKPOINT_ONLY', 'ADVANCE_SHIPMENT', 'BBX_CHILDREN', 'SHIPMENT_DETAILS_ONLY']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/LevelOfDetails' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/PiecesEnabled', mode="before")
    @classmethod
    def _validate_TrackingRequest_PiecesEnabled_96(cls, v: Any) -> Any:
        """Optional; allowed values B, S, P; default B"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['B', 'S', 'P']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/PiecesEnabled' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/EstimatedDeliveryDateEnabled', mode="before")
    @classmethod
    def _validate_TrackingRequest_EstimatedDeliveryDateEnabled_97(cls, v: Any) -> Any:
        """Optional; allowed values 1 (true), 0 (false)"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['1', '0']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/EstimatedDeliveryDateEnabled' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/RequestControlledAccessDataCodes', mode="before")
    @classmethod
    def _validate_TrackingRequest_RequestControlledAccessDataCodes_98(cls, v: Any) -> Any:
        """Optional; allowed values 1 (true), 0 (false)"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['1', '0']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/RequestControlledAccessDataCodes' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/RequestControlledAccessData', mode="before")
    @classmethod
    def _validate_TrackingRequest_RequestControlledAccessData_99(cls, v: Any) -> Any:
        """Optional; allowed values 1 (true), 0 (false)"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['1', '0']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/RequestControlledAccessData' must be one of {allowed}; got {v!r}")
        return v

    @field_validator('TrackingRequest/RequestGMTOffsetPerEvent', mode="before")
    @classmethod
    def _validate_TrackingRequest_RequestGMTOffsetPerEvent_100(cls, v: Any) -> Any:
        """Optional; allowed values 1 (true), 0 (false)"""
        if v is None:
            return v
        s = str(v).strip() if v != "" else ""
        if s == "":
            return v
        allowed = ['1', '0']
        if v not in allowed and s not in allowed:
            raise ValueError(f"'TrackingRequest/RequestGMTOffsetPerEvent' must be one of {allowed}; got {v!r}")
        return v
