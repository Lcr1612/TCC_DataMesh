CREATE OR REPLACE FUNCTION public.fn_data_atualizacao()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_entrega_data_atualizacao
BEFORE UPDATE ON public.entrega
FOR EACH ROW
EXECUTE FUNCTION public.fn_data_atualizacao();